from .base import *  # noqa
from .base import env


# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': env.str('DB_DEFAULT_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': env.str('DB_DEFAULT_DBNAME', default='dev_roon_default.primary.sqlite3.db'),
        'USER': env.str('DB_DEFAULT_USER', default=''),
        'PASSWORD': env.str('DB_DEFAULT_PASSWORD', default=''),
        'HOST': env.str('DB_DEFAULT_HOST', default=''),
        'PORT': env.int('DB_DEFAULT_PORT', default=0),
    },
    'replica_db': {
        'ENGINE': env.str('DB_REPLICA_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': env.str('DB_REPLICA_DBNAME', default='dev_roon_default.primary.sqlite3.db'),
        'USER': env.str('DB_REPLICA_USER', default=''),
        'PASSWORD': env.str('DB_REPLICA_PASSWORD', default=''),
        'HOST': env.str('DB_REPLICA_HOST', default=''),
        'PORT': env.int('DB_REPLICA_PORT', default=0),
        'TEST': {
            'MIRROR': 'default',
        },
    },
}

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env.str(
    "DJANGO_SECRET_KEY",
    default="GpgYRTCDwHrLA3XWnj8wZT7tTuVZu2ZX5jdaRA2gUd6XrNnSsbsDgoDYA1jowD7x",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env.str(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)

# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
if env.bool("USE_DOCKER", default=False):
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]  # noqa F405

# Your stuff...
# ------------------------------------------------------------------------------
