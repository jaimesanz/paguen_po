Deployment
==========

This guide shows how to deploy the application using Amazon Web Services.

EC2 instance
------------

Create an EC2 instance (Ubuntu 16.04), and create the proper SSH keys. Download the `.pem` file and store
it in a safe location.

Connect to the instance vía ssh::

    ssh -i "<private key (.pem) file>" <instance's public DNS>

Clone the repo and create the proper virtualenv. Then install the proper requirements into it. The directory
should look something like this:

.. code-block:: python

    paguen_po/  # repo's root
        ...
        venv/
        paguen_po/
            ...
            config/
                ...
                wsgi.py
            manage.py


Install the proper version of apache and mod_wsgi. For **python 2**::

    sudo apt-get install python-pip apache2 libapache2-mod-wsgi

For **python 3**::

    sudo apt-get install python3-pip apache2 libapache2-mod-wsgi-py3

Edit the apache configuration file `/etc/apache2/sites-available/000-default.conf`. Make sure to use the
proper python version.

.. code-block:: apache

    <VirtualHost *:80>
        ...

        ServerAdmin webmaster@localhost
        DocumentRoot /var/www/html

        ...

        Alias /static /home/ubuntu/paguen_po/paguen_po/static_root
        <Directory /home/ubuntu/paguen_po/paguen_po/static_root>
            Require all granted
        </Directory>

        Alias /media /home/ubuntu/paguen_po/paguen_po/media
        <Directory /home/ubuntu/paguen_po/paguen_po/media>
            Require all granted
        </Directory>

        <Directory /home/ubuntu/paguen_po/paguen_po/config>
            <Files wsgi.py>
                Require all granted
            </Files>
        </Directory>

        WSGIDaemonProcess paguen_po python-home=/home/ubuntu/paguen_po/venv/lib/python3.5/site-packages python-path=/home/ubuntu/paguen_po/paguen_po
        WSGIProcessGroup paguen_po
        WSGIScriptAlias / /home/ubuntu/paguen_po/paguen_po/config/wsgi.py
        ...
    </VirtualHost>

.. important::

    In order to access the server, you have to configure the security group of the EC2 instance to allow
    access on port 80. To do this, go to EC2 instances, and then select the *Security Groups* tab on the
    left panel. Then find the security group that the instance is in, and edit the *Inbound* tab, and add a
    rule to allow HTTP access.

Finally, restart the apache2 service::

    sudo service apache2 restart

.. seealso::

    https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-apache-and-mod_wsgi-on-ubuntu-16-04
    https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/modwsgi/#basic-configuration

Database
--------

The easiest way is to configure the PostgreSQL database in the same EC2 instance. To do this, follow the same
instructions as for the development server.

For a proper production server, configure a RST instance running PostgreSQL.

Either way, after configuring the database, edit the `secrets.json` file and add the proper database
credentials.

Simple Email Service (SES)
--------------------------

To use SES, two libraries are needed: ``boto`` and ``django-ses`` (both libraries are included in
the requirement files). ``boto`` is a a large python package that gives control over many AWS
services, including SES.

We need to provide ``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY`` in the settings file for
boto to access the services:

.. code-block:: python

   AWS_ACCESS_KEY_ID = 'YOUR-ACCESS-KEY-ID'
   AWS_SECRET_ACCESS_KEY = 'YOUR-SECRET-ACCESS-KEY'

.. important::

   Since the only service we want to use with boto is SES, it would be foolish to use the master
   id/key pair. We should create an IAM user only with enough permissions to use SES, and
   generate an access id/key pair for that user. **This is the key used in the settings file.**

   To create the IAM user, follow official instructions: http://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html

.. seealso::

   * https://hmarr.com/2011/jan/26/using-amazons-simple-email-service-ses-with-django/
   * https://github.com/boto/boto3

DNS and Route 53
----------------
To configure the dns (for instance, for NIC Chile), use the Route 53 service. Go to hosted
zones (Route 53 -> Hosted Zones) and create a new hosted zone with the desired domain name.
Then, you need to allocate an elastic IP for the EC2 instance running apache. To do this, go to:

EC2 -> Network & Security -> Elastic Ips

Afterwards, go back to hosted zones and create the following records in the hosted zone you created
earlier:

- create an A record pointing DOMAIN_NAME to ELASTIC_IP.
- create an A record pointing www.DOMAIN_NAME to ELASTIC_IP.

This zone is now pointing to the elastic IP! Finally, the primary and secondary DNSs are in the
NS record of the hosted zone. Use these DNSs to fill out whatever form the DNS provider
(NIC Chile) needs.

.. seealso::

    http://serverfault.com/questions/551767/how-do-i-set-up-dns-with-nic-io-to-point-to-an-aws-ec2-server

