# Roon-API

Question and Answer Querying API

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

License: MIT

## Discussion

### Authentication
- I added authn + authz to the repo. However, I would recommend that authn be handled by a third-party system, such as AWS Cognito or Okta
  - Moving to third-party systems means that passwords would not need to be stored in our DBs, which would be safer
  - I would implement a stateless authentication (JWT) with provided scopes.
    - This will allow for future microservices expansion
    - With asymmetric authentication, decrease load on the system for authn
- Authz was also implemented, using Django's authz support. 
  - Each endpoint is decorated with the authz creds that the user needs to enter the endpoint
  - Also, a group(s) should be implemented and handled by an Auth service. This could communicate with Okta to add scopes within the JWT that is issued

### Bottlenecks
- Django would not be an issue for upto 1M+ customers. 
  - With resources in the cloud, we can always horizontally autoscale the service to meet demand
  - However, if we want more control of parts of Django (ORM, Authentication Backend, etc ...), then you may want to move a lighter framework (FastAPI, Flask, Sanic, etc ...)
- Caching
  - I don't believe caching would need to be implemented, unless more expressive and complex search behavior is added
    - N-Gram, Frequency mode, and other fuzzy searching capabilities would better be served by Elasticsearch
  - We can regionally replicate the Postgres DB and use the read replicas to decrease latency for data access patterns
  - If one is needed, a distributed cache would be best (Redis)
    - Implement a write-behind cache that updates the cache async, decreases write complexity and overhead 
- Moving off REST
  1) FE needs to make multiple REST calls to render a page and stitch the data together
  2) I would move off of REST once more complicated service-to-service communication arises that needs data aggregation (Microservices)
  3) Versioning of endpoints starts to arise across the Microservice layers

### Search
- Full search, with OR, NOT, IN operations. 
  - I also added an approach to ADVANCED searches (doing a combination of OR/AND searches)
- Full-Text Search
  - Use SearchVector for all available fields to search against
  - To speedup performance can add `SearchVectorField`, but this adds space to the DB and would also need to be migrated if the fields change


        search_qs = (
            Quote.objects.annotate(
                search=search_vector, rank=SearchRank(search_vector, search_query)
            )
            .filter(search=search_query)
            .order_by("-rank")
        )

    



## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Setting Up Your Users

-   To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

-   To create a **superuser account**, use this command:

        $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy roon_api

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

## Deployment

The following details how to deploy this application.

### Docker

See detailed [cookiecutter-django Docker documentation](http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html).
