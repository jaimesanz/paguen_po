Installation
============

Configuring PostgreSQL
----------------------
This instructions were taken from `Justin Ellingwood's tutorial <https://www.digitalocean.com/community/tutorials/how-to-use-postgresql-with-your-django-application-on-ubuntu-14-04/>`_:

* install components:

    .. code-block:: bash

        sudo apt-get update
        sudo apt-get install python-pip python-dev libpq-dev postgresql postgresql-contrib

* enter postgres shell:

    .. code-block:: bash

        sudo su - postgres
        psql

* create database and just permissions:

    .. code-block:: psql

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

        sudo apt-get install python3-dev libjpeg-dev

To export the virtualenv:

    .. code-block:: bash

        pip freeze > requirements/dev.txt

To create a new virtualenv using requirements/dev.txt, create virtualenv (this makes sure to
use the virtualenv for python3):

    .. code-block:: bash

        virtualenv -p python3 <env_name>

then activate it

    .. code-block:: bash

        source <env_name>/bin/activate

and finally install the requirements

    .. code-block:: bash

        pip install -r requirements/dev.txt

Fixtures
--------
Before running the server, you must load all basic fixtures. To do this, you should run this command:

.. code-block:: bash

    python manage.py loaddata vivs.json

Static Files & Yarn
-------------------
Finally, before running the server you need the front-end dependencies. Most external static files are
handled using `yarn <https://yarnpkg.com/en/>`_. All the dependencies are listed in a file called
``package.json``, which can be found at the project's root.

To use yarn, first you need to install `NodeJS <https://nodejs.org/en/>`_:

.. code-block:: bash

    # in Ubuntu/Debian
    curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
    sudo apt-get install -y nodejs

Now you can install yarn by running:

.. code-block:: bash

    # in Ubuntu/Debian
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
    sudo apt-get update && sudo apt-get install yarn

Finally, you can install all dependencies by running:

.. code-block:: bash

    yarn

.. important::

    For this to work, you have to be in the project's root folder, because that's where the
    ``package.json`` file (which contains the list of dependencies) is.

.. seealso::

    * `Installing NodeJS 8 on Debian/Ubuntu
      <https://nodejs.org/en/download/package-manager/#debian-and-ubuntu-based-linux-distributions>`_
    * `Installing Yarn <https://yarnpkg.com/en/docs/install>`_
