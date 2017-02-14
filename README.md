[![Build Status](https://travis-ci.org/jaimesanz/paguen_po.svg?branch=master)](https://travis-ci.org/jaimesanz/paguen_po)

PaguenPo
=============

"PaguenPo" (roughly translated to "PayUp" or "DudesComeOnPayMeAlready") is a web application developed to solve a variety of problems that arise from living with roommates. From balancing the contributions of the users to the common purse, to generating statistics about the monthly expenses of the group. It runs on Python 3.4.3 using the Django framework along with PostgresSQL.

This project is also the Thesis of https://github.com/jaimesanz

Installation
-------------
The instructions to install the aplication can be found in the install_files/ directory. After following those instructions, you have to specify the secret settings for the project. To do this, fill out the empty fields in settings_secret.py.template, and then rename it to settings_secret.py

Expenses
-------------
Create new Expenses for the Household. Expenses are associated with a specific Category, which can be customized by the roommates. This way, users can decide which Categories should be always shared, and which ones are not supposed to be shared when one of the users is not living in the Household for a long period of time. A neat set of graphs is also provided so that users can see how much they've spent in each period and each category. This could later be used to define appropiate budgets per period. 

Vacations
-------------
Users can define periods of time when they will not be living in the Household. This will become useful later on, when the users make use of the Balancing feature. Vacations are neccesary because there are certain Expenses that should be payed even by users who are out by the time of the Expense. One example of this is the rent.

Budgets
-------------
Budgets are meant to help users make a plan of investments for each category for each period, and therefore make better use of their resources.

Lists
-------------
Users can define Lists of Items that are missing in the Household. Then, any other user can "fill out" this List by marking each Item as "bought". Afterwards, an Expense is created for that user, specifying the Items that the user bought, and how much he spent on that particular List. Users can also define their own set of Items needed in the Household.

Balance
-------------
Once users have all spent money on different categories or lists, they'll want to balance out the expenses so that everyone has actually contributed the same to the common purse. The balance feature is meant to solve this problem: given a set of Expenses made by the active users, a set of instructions is generated. The instructions follow this format:

<strong>User1 must transfer X to User2.</strong>

Note that this does not actually make the transfer happen, it's only meant to give the users an idea of how to balance everything out.

Transfer
-------------
Once the instructions for balancing have been generated, users can actually "transfer" funds to one another. In reality, users are going to balance everything, but outside the system. The transactions are just meant to tell the system that users (in RL) have already balance the expenses.
