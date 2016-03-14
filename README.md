# admin_gastos

Configuring PostgreSQL:
source: https://www.digitalocean.com/community/tutorials/how-to-use-postgresql-with-your-django-application-on-ubuntu-14-04

install components:
sudo apt-get update
sudo apt-get install python-pip python-dev libpq-dev postgresql postgresql-contrib

create database and database user:
sudo su - postgres

enter postgres shell:
psql

CREATE DATABASE admin_gastos;
CREATE USER myprojectuser WITH PASSWORD 'password';
