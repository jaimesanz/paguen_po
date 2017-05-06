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
