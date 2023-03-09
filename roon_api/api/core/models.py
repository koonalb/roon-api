"""Core model definitions for phi service"""
import abc
import ast
import operator
from datetime import datetime
from functools import reduce

from dateutil.parser import parse
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import QueryDict

from api.core.exceptions import DateSearchError, SearchWithOperatorException
from api.core.utils import computed_model_keys, model_search, remove_forbidden_data

SEARCH_FILTERS = settings.SEARCH_FILTERS


def error_constructor(message, **optional_errors):
    """
    Defines error structuring content
    """

    base_error = {"success": False, "error_reason": message}
    if optional_errors:
        base_error.update(optional_errors)
    return base_error


class EagerLoadingMixin(object):
    """
    Mixin for queryset optimizations
    """

    @classmethod
    def setup_eager_loading(cls, queryset):

        # select_related for "to-one" relationships
        if hasattr(cls, "_SELECT_RELATED_FIELDS"):
            queryset = queryset.select_related(*cls._SELECT_RELATED_FIELDS)
        # prefetch_related for "to-many" relationships
        if hasattr(cls, "_PREFETCH_RELATED_FIELDS"):
            queryset = queryset.prefetch_related(*cls._PREFETCH_RELATED_FIELDS)
        return queryset


class TransformComputedParams(object):
    """
    The API outputs data that does not mimic the database (serializer or model
    properties), so some parameters and/or values are transformed into database
    readable inputs.
    """

    def __init__(self, params, model):

        assert isinstance(params, (QueryDict, dict))
        # Turn on mutability of QueryDict
        self._params = params.copy()

        # Initial Model used
        self._initial_model_class = model
        self._params_transform = self._initial_model_class.param_transform()

        self.all_nested_models = set()
        self.nested_models = {}

        # Initial transform state
        initial_tuple = (self._initial_model_class.__name__, self._initial_model_class)
        self._model_relationship_traverse(self._initial_model_class, [initial_tuple])

    def process_params(self):
        """
        Execute params transform
        """

        if not self._params:
            return self._params

        # Add plugins here
        self._boolean_transform(self._initial_model_class)
        self._pull_params_transform(bool_search=self._boolean_transform)
        self._transform_params()

        return self._params

    def process_boolean_params(self, additional_params=None):
        """
        Iterate thru self._params and transform all boolean values.
        This method uses the DB models (self.all_nested_models) built in ctr.
        """

        for nested_name, nested_model_class in self.all_nested_models:
            try:
                self._boolean_transform(nested_model_class, nested_name)
            except AttributeError:
                # Object does not transform - likely due to Django's own model
                # object, Ex: Groups
                pass

        if additional_params:
            assert isinstance(additional_params, list)
            for param in additional_params:
                param_value = self._params.get(param, False)
                if self._is_true(param_value):
                    self._params[param] = 1
                elif self._is_false(param_value):
                    self._params[param] = 0
                else:
                    raise ValueError("%s has invalid boolean field value of %s" % (additional_params, param_value))
        return self._params

    def get_nested_models_for_validation(self):
        """
        Used to test model attribute validity in other methods
        Ex: date_search
        """

        # All the nested models used for the param transform
        return self.nested_models

    def _model_relationship_traverse(self, model_class, models_queue):
        """
        Find all model relationships associated with the initial model
        NOTE: that this method adds entries to the cls.all_nested_models
        """

        try:
            model_fields = model_class._meta.fields

            # Foreign Key Objects
            foreignkey_models = [
                (fk.name, model_class._meta.get_field(fk.name).remote_field.model)
                for fk in model_fields
                if fk.get_internal_type() in ("ForeignKey", "OneToOneField")
            ]
            models_queue.extend([tup for tup in foreignkey_models if tup not in self.all_nested_models])

            # Related Objects
            rel_objects = [
                f
                for f in model_class._meta.get_fields()
                if (f.one_to_many or f.one_to_one) and f.auto_created and not f.concrete
            ]
            related_obj_models = [(k.related_name, k.related_model) for k in rel_objects if k.related_name]
            models_queue.extend([tup for tup in related_obj_models if tup not in self.all_nested_models])

        except Exception as err:
            return False

        try:
            model_class = models_queue[-1][1]
            self.all_nested_models.update(models_queue)
            self._model_relationship_traverse(model_class, models_queue[:-1])
        # No more objects to process
        except IndexError:
            return True

    def _pull_params_transform(self, **transform_plugins):
        """
        Get param_transform() for all associated
        models and transform params for plugins
        """

        for nested_name, nested_model_class in self.all_nested_models:
            try:
                fk_params = nested_model_class.param_transform()
                prefix = nested_name + "__"
                self._params_transform.update({prefix + k: prefix + v for k, v in fk_params.items()})

                # Models used - primarily for model validation
                self.nested_models[prefix] = nested_model_class

                # Use any transform plugins
                for plugin_transform in list(transform_plugins.values()):
                    plugin_transform(nested_model_class, nested_name)

            except AttributeError:
                # Object does not transform - likely
                # due to Django's own model object
                # Ex: Groups
                pass

    def _transform_params(self):
        """
        Transform initial params input with the new transform

        1, for entry in cls.param_transform,
         if in self._param change key to transform-key
        2, do #1 for order_by key (if exist), and changes its value

        """
        if bool(set(self._params.keys()).intersection(list(self._params_transform.keys()))):
            for key in list(self._params.keys()):
                if key in self._params_transform:
                    new_key = self._params_transform.get(key)
                    self._params.setlist(new_key, self._params.pop(key))
                    continue

        # process order_by if any
        val_order_by = self._params.get("order_by", None)
        if val_order_by:
            for key in self._params_transform:
                if key in val_order_by:
                    self._params["order_by"] = val_order_by.replace(key, self._params_transform[key])
                    break

    ###
    # Add plugins here
    ###

    def _boolean_transform(self, model, fk_name=None):
        """
        Transform boolean field in the model into database readable inputs
        NOTE: if an boolean field has invalid value, raise ValueError.
        """

        boolean_list = [bf.name for bf in model._meta.fields if bf.get_internal_type() == "BooleanField"]
        for bool_field in boolean_list:
            if bool_field not in list(self._params.keys()):
                if not fk_name:
                    continue  # nothing to do
                bool_field = fk_name + "__" + bool_field
                if bool_field not in list(self._params.keys()):
                    continue

            if self._is_true(self._params[bool_field]):
                self._params[bool_field] = 1
            elif self._is_false(self._params[bool_field]):
                self._params[bool_field] = 0
            else:
                raise ValueError("%s has invalid boolean field value of %s" % (bool_field, self._params[bool_field]))

    @staticmethod
    def _is_true(val):
        return str(val).lower() in ["true", "1", "t", "y", "yes"]

    @staticmethod
    def _is_false(val):
        return str(val).lower() in ["false", "0", "f", "n", "no"]


def date_search(model, query_dictionary):
    """
    Check and return a queryset if a date search is being conducted
    """

    attribute_filter_item = start_time = end_time = filter_param = time = None
    skip_attribute_check = False

    # Turn on mutability of QueryDict
    query_dictionary = query_dictionary.copy()

    delete_keys = []
    for key, value in list(query_dictionary.items()):
        if "date_start" in key:
            attribute_filter_item = key.rsplit("_", 2)[0]
            try:
                start_time = parse(value, ignoretz=True)
            except Exception:
                raise DateSearchError("For date search, please format datetime " "as follows: YYYY-MM-DDTH:M:S")
            time = start_time
            filter_param = "__gte"
            delete_keys.append(key)
        elif "date_end" in key:
            # Only check the end_time attribute if one has not been set
            # If it has, use the start_time attribute
            if attribute_filter_item is None:
                attribute_filter_item = key.rsplit("_", 2)[0]
            try:
                end_time = parse(value, ignoretz=True)
            except Exception:
                raise DateSearchError("For date search, please format datetime " "as follows: YYYY-MM-DDTH:M:S")
            time = end_time
            filter_param = "__lte"
            delete_keys.append(key)

    for key in delete_keys:
        del query_dictionary[key]

    # Check if date search is being conducted, if not return the model
    if not time:
        return model, query_dictionary

    # Check if param needs to be transformed,
    #  if so the model validation is removed
    prefix = ""
    model_class = model.model
    transform_params = TransformComputedParams({attribute_filter_item: attribute_filter_item}, model_class)
    transformed_attribute = list(transform_params.process_params().keys())[0]
    nested_models = transform_params.get_nested_models_for_validation()

    # Check for Date Search on a property
    if transformed_attribute != attribute_filter_item:
        attribute_filter_item = transformed_attribute
        skip_attribute_check = True
    # Check for nested Date Search
    else:
        # Makes sure nested value search is exact
        split_attrs = [attr + "__" for attr in transformed_attribute.split("__")][:1]
        for key in list(nested_models.keys()):
            if {key}.intersection(set(split_attrs)):
                model_class = nested_models[key]()
                prefix = key
                attribute_filter_item = attribute_filter_item.replace(prefix, "")
                continue

    # Check if a valid attribute was supplied
    if not skip_attribute_check:
        if not hasattr(model_class, attribute_filter_item):
            raise DateSearchError("For date search, a valid model " "attribute needs to be provided.")
        datetime_attr = model_class._meta.get_field(attribute_filter_item).get_internal_type() in (
            "DateTimeField",
            "DateField",
        )
        if not datetime_attr:
            raise DateSearchError("For date search, a valid datetime model " "attribute needs to be provided.")

    # Check for a date range
    if all((start_time, end_time)):
        attribute_filter_item = prefix + attribute_filter_item
        if start_time < end_time:
            return (model.filter(**{attribute_filter_item + "__range": [start_time, end_time]}), query_dictionary)
        else:
            raise DateSearchError("For date range search, the date_end " "has to be greater than the date_start.")
    # Conducting a start or end date search
    else:
        attribute_filter_item = prefix + attribute_filter_item
        return (model.filter(**{attribute_filter_item + filter_param: time}), query_dictionary)


def search_with_operator(qs, query_dictionary):
    """
    Parse initial params for search
    """
    try:
        if type(query_dictionary) is not dict:
            # QuerySets do not return lists of values
            # well: turn to python dictionary
            query_dictionary = dict(query_dictionary.lists())
            opr = query_dictionary.pop("operator")[0].upper()
        else:
            opr = query_dictionary.pop("operator").upper()

        # Return if no params provided.
        if not query_dictionary or set(query_dictionary.keys()).issubset(set(SEARCH_FILTERS)):
            return qs

        if opr == "IN":
            for param in list(query_dictionary.keys()):
                return getattr(qs, opr)(param, query_dictionary[param])
        else:
            cleaned_query_dictionary = remove_forbidden_data(query_dictionary, SEARCH_FILTERS)
            return getattr(qs, opr)(cleaned_query_dictionary)

    except Exception as err:
        raise SearchWithOperatorException(err)


class CustomModelQuerySet(QuerySet):
    """
    Custom QS Manager
    """

    ALLOWED_OPERATIONS = ["_OR", "_AND", "_NOT"]

    def query_creation(self, query_dict):
        """
        Takes list or dict of 'query_strings'.
        """

        def query_creation_helper(_query_dict, q_objects):
            for key in _query_dict:

                # Iterate over a list of the same command
                # ex: {_AND: [_OR: {}, _OR: {}]}
                if isinstance(_query_dict, list):
                    for item in _query_dict:
                        query_creation_helper(item, q_objects)
                    break

                if key in self.ALLOWED_OPERATIONS:
                    # Add Reduced Q Node Tree
                    q_objects.append(getattr(self, key)(_query_dict[key]))
                    continue

                if isinstance(_query_dict[key], list):
                    for item in _query_dict[key]:
                        query_creation_helper({key: item}, q_objects)
                else:
                    q_objs = model_search({key: _query_dict[key]}, qs=None, qs_objs=True)
                    q_objects.extend(q_objs)

            return q_objects

        return query_creation_helper(query_dict, [])

    def build_qs(self, q_objs):
        """
        Build from supplied Q Objects
        """
        qs = self.filter(q_objs).filter(is_active=True)

        return qs

    def _AND(self, query_dict):
        return reduce(operator.and_, self.query_creation(query_dict))

    def _OR(self, query_dict):
        return reduce(operator.or_, self.query_creation(query_dict))

    def _NOT(self, query_dict):
        return ~(reduce(operator.or_, self.query_creation(query_dict)))

    def AND(self, query_dict):
        """
        Same as Django's filter method
        """
        return self.build_qs(self._AND(query_dict))

    def OR(self, query_dict):
        """
        Returns a QuerySet containing all objects that
        satisfy the predicates within *args
        """
        return self.build_qs(self._OR(query_dict))

    def NOT(self, query_dict):
        """
        Returns a QuerySet containing all objects that
        do not satisfy the predicates within *args
        """
        return self.build_qs(self._NOT(query_dict))

    def IN(self, field, values):
        """
        Returns a QuerySet containing all objects that
        satisfy the predicates within **kwargs' values
        """
        return self.build_qs(Q((field + "__in", values)))

    def ADVANCED(self, query_dict):
        """
        Returns a complex QuerySet
        """
        operation_keys = [key for key in query_dict.keys() if key in self.ALLOWED_OPERATIONS]

        if operation_keys:
            if len(operation_keys) > 1:
                raise SearchWithOperatorException(
                    "Invalid usage of Advanced search. You have sent: {}. "
                    'Choose only one "outer" operation'.format(operation_keys)
                )
            else:
                operation = operation_keys[0]
                decoded_query = []
                if isinstance(query_dict[operation], list):
                    decoded_query = [ast.literal_eval(data) for data in query_dict[operation]]
        else:
            raise SearchWithOperatorException(
                "Invalid usage of Advanced search. You have not sent an"
                ' operation. Choose one "outer" operation Ex: {}'.format(self.ALLOWED_OPERATIONS)
            )

        return self.build_qs(getattr(self, operation)(decoded_query))


class CustomModelManager(models.Manager):
    def get_queryset(self):
        return CustomModelQuerySet(self.model, using=self._db).all()

    def AND(self, *args):
        """
        Same as Django's filter method
        """
        # pylint:disable=E1120
        return self.get_queryset().AND(*args)

    def OR(self, *args):
        """
        Returns a QuerySet containing all objects that
        satisfy the predicates within *args
        """
        # pylint:disable=E1120
        return self.get_queryset().OR(*args)

    def NOT(self, *args):
        """
        Returns a QuerySet containing all objects that
        do not satisfy the predicates within *args
        """
        # pylint:disable=E1120
        return self.get_queryset().NOT(*args)

    def IN(self, **kwargs):
        """
        Returns a QuerySet containing all objects that
        satisfy the predicates within **kwargs' values
        """
        return self.get_queryset().IN(**kwargs)

    def ADVANCED(self, *args):
        """
        Returns a complex QuerySet
        """
        # pylint:disable=E1120
        return self.get_queryset().ADVANCED(*args)


class ActiveModelManager(CustomModelManager):
    def get_queryset(self):
        return CustomModelQuerySet(self.model, using=self._db).filter(is_active=True)


class InactiveModelManager(CustomModelManager):
    def get_queryset(self):
        return CustomModelQuerySet(self.model, using=self._db).filter(is_active=False)


class CoreModel(models.Model):
    """
    An abstract class that contains general data throughout models.

    """

    # History
    created_at = models.DateTimeField("Created At", blank=True, default=datetime.utcnow, db_index=True)
    last_modified = models.DateTimeField("Last Modified At", blank=True, default=datetime.utcnow, db_index=True)
    is_active = models.BooleanField("Is Active", default=True, db_index=True)
    deactivated_at = models.DateTimeField("Deactivated At", blank=True, default=datetime.min)

    @property
    def active(self):
        return self.is_active

    @active.setter
    def active(self, value):
        self.deactivated_at = datetime.min if value else datetime.utcnow()
        self.is_active = value

    @abc.abstractmethod
    def param_transform(self):
        """
        Input parameter transform for either
        model or serializer computed properties
        """

        raise NotImplementedError("Each Django model needs to have params_transform defined")

    @classmethod
    def model_keys(cls):
        """
        List of attributes associated with this model class
        """

        return computed_model_keys(cls, field_name_exclusions=[], field_type_exclusions=[])

    # Managers
    objects = CustomModelManager()  # Default
    active_objects = ActiveModelManager()  # Active objects only
    inactive_objects = InactiveModelManager()

    class Meta:
        abstract = True
