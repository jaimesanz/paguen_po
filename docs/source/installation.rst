Installation
============

Before doing anything, make sure you have python 3.4 and pip installed.

Configuring PostgreSQL
----------------------
This instructions were taken from `Justin Ellingwood's tutorial
<https://www.digitalocean.com/community/tutorials/how-to-use-postgresql-with-your-django-application-on-ubuntu-14-04/>`_:

Install dependencies:

.. code-block:: bash

    sudo apt-get update
    sudo apt-get install libpq-dev postgresql postgresql-contrib

Enter postgres shell:

.. code-block:: bash

    sudo su - postgres
    psql

Create database and just permissions:

.. code-block:: psql

    CREATE DATABASE ``DB_NAME``;
    CREATE USER ``MYPROJECTUSER`` WITH PASSWORD '``PASSWORD``';
    ALTER ROLE ``MYPROJECTUSER`` SET client_encoding TO 'utf8';
    ALTER ROLE ``MYPROJECTUSER`` SET default_transaction_isolation TO 'read committed';
    ALTER ROLE ``MYPROJECTUSER`` SET timezone TO 'UTC';
    GRANT ALL PRIVILEGES ON DATABASE ``DB_NAME`` TO ``MYPROJECTUSER``;
    \q
    exit

Now we need to tell Django to use this database. To do this, we need to fill the project's
secrets file:

.. code-block:: bash

    cp paguen_po/config/secrets.json.example paguen_po/config/secrets.json
    nano paguen_po/config/secrets.json

Change database settings to this:

.. code-block:: python

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'DB_NAME',
            'USER': 'MYPROJECTUSER',
            'PASSWORD': 'PASSWORD',
            'HOST': 'localhost',
            'PORT': '',
        }
    }


Virtual Environment
-------------------
Before installing anything, run this commands, or there will be problems installing some libraries:

    .. code-block:: bash

        sudo apt-get install python3-dev libjpeg-dev

To create a new virtualenv using requirements/dev.txt, create virtualenv (the ``-p python3`` makes
sure to use the virtualenv for python3):

    .. code-block:: bash

        virtualenv -p python3 ``<VENV_NAME>``

then activate it

    .. code-block:: bash

        source ``<VENV_NAME>``/bin/activate

and finally install the requirements

    .. code-block:: bash

        pip install -r requirements/dev.txt

Populating the Database
-----------------------
Finally, you need to create the tables in the database. To do this, run:

.. code-block:: bash

    python paguen_po/manage.py migrate

And finally, create a superuser:

.. code-block:: bash

    python paguen_po/manage.py createsuperuser

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
