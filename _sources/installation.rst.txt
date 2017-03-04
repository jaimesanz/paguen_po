Installation
============

Configuring PostgreSQL
----------------------

This instructions were taken from `Justin Ellingwood's tutorial <https://www.digitalocean.com/community/tutorials/how-to-use-postgresql-with-your-django-application-on-ubuntu-14-04/>`_:

* install components:

    .. code-block:: bash

        sudo apt-get update
        sudo apt-get install python-pip python-dev libpq-dev postgresql postgresql-contrib

* create database and database user:

    .. code-block:: bash

        sudo su - postgres

* enter postgres shell:

    .. code-block:: bash

        psql

* create database and just permissions:

    .. code-block:: bash

        CREATE DATABASE admin_gastos;
        CREATE USER myprojectuser WITH PASSWORD 'password';
        ALTER ROLE myprojectuser SET client_encoding TO 'utf8';
        ALTER ROLE myprojectuser SET default_transaction_isolation TO 'read committed';
        ALTER ROLE myprojectuser SET timezone TO 'UTC';
        GRANT ALL PRIVILEGES ON DATABASE admin_gastos TO myprojectuser;
        \q
        exit

* enter virtualenv:

    .. code-block:: bash

        source admin_gastos/bin/activate

* install psycopg2:

    .. code-block:: bash

        pip install psycopg2

* edit project settings:

    .. code-block:: bash

        nano ~/admin_gastos/project_root/settings.py

* change database settings to this:

    .. code-block:: python

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'myproject',
                'USER': 'myprojectuser',
                'PASSWORD': 'password',
                'HOST': 'localhost',
                'PORT': '',
            }
        }

* migrate:

    .. code-block:: bash

        python manage.py makemigrations
        python manage.py migrate

* create super user:

    .. code-block:: bash

        python manage.py createsuperuser

Virtual Environment
-------------------

Before installing anything, run this commands, or there will be problems installing some libraries:

    .. code-block:: bash

        sudo apt-get install python3-dev
        sudo apt-get install libjpeg-dev

To export the virtualenv:

    .. code-block:: bash

        pip freeze > requirements/dev.txt

To create a new virtualenv using requirements/dev.txt, create virtualenv (this makes sure to
use the virtualenv for python3):

    .. code-block:: bash

        virtualenv -p python3 <env_name>

, then activate it

    .. code-block:: bash

        source <env_name>/bin/activate

, and finally install the requirements

    .. code-block:: bash

        pip install -r requirements/dev.txt

Fixtures
--------
Before running the server, you must load all basic fixtures. To do this, you should run this command:

    .. code-block:: bash

        python manage.py loaddata vivs.json