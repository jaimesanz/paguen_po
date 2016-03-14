Configuring PostgreSQL:
source: https://www.digitalocean.com/community/tutorials/how-to-use-postgresql-with-your-django-application-on-ubuntu-14-04

1.- install components:
sudo apt-get update
sudo apt-get install python-pip python-dev libpq-dev postgresql postgresql-contrib

2.- create database and database user:
sudo su - postgres

3.- enter postgres shell and do stuff:
psql

CREATE DATABASE admin_gastos;
CREATE USER myprojectuser WITH PASSWORD 'password';
ALTER ROLE myprojectuser SET client_encoding TO 'utf8';
ALTER ROLE myprojectuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE myprojectuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE admin_gastos TO myprojectuser;
\q
exit

4.- enter virtualenv:
source admin_gastos/bin/activate

5.- install psycopg2:
pip install psycopg2

6.- edit project settings:
nano ~/admin_gastos/mysite/settings.py

7.- change database settings to this:
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

8.- migrate:
python manage.py makemigrations
python manage.py migrate

9.- create super user:
python manage.py createsuperuser

