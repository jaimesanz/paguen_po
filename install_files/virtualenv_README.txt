# NOTE: before installing anything, run this command:
sudo apt-get install python3-dev

#######################
to export the virtualenv:
pip freeze > requirements.txt

to create a new virtualenv using requirements.txt:
# cd to project root
virtualenv <env_name>
source <env_name>/bin/activate
pip install -r requirements.txt

