[![Build Status](https://travis-ci.org/jaimesanz/paguen_po.svg?branch=master)](https://travis-ci.org/jaimesanz/paguen_po)
[![Coverage Status](https://coveralls.io/repos/github/jaimesanz/paguen_po/badge.svg?branch=master)](https://coveralls.io/github/jaimesanz/paguen_po?branch=master)
[![Requirements Status](https://requires.io/enterprise/jaimesanz/paguenpo/requirements.svg?branch=master)](https://requires.io/enterprise/jaimesanz/paguenpo/requirements/?branch=master)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://github.com/jaimesanz/paguen_po/blob/master/LICENSE.md)
[![Python Version](https://img.shields.io/badge/python-3.5.2-brightgreen.svg)](https://www.python.org/)


PaguenPo
=============

"PaguenPo" (roughly translated to "PayUp" or "DudesComeOnPayMeAlready") is a web application developed to solve a variety of problems that arise from living with roommates. From balancing the contributions of the users to the common purse, to generating statistics about the monthly expenses of the group. It runs on Python 3.5.2 using the Django framework along with PostgreSQL.

Installation
-------------
For detailed installation instructions, follow the [relevant documentation](http://jaimesanz.github.io/paguen_po/installation.html). After that, you have to specify the secret settings for the project. To do this, fill out the empty fields in `settings_secret.py.template`, and then rename it to `settings_secret.py`