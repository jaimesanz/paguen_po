# NOTE: before installing anything, run this commands, or there will be
problems installing some libraries:
sudo apt-get install python3-dev
sudo apt-get install libjpeg-dev

#######################
to export the virtualenv:
pip freeze > install_files/requirements.txt

to create a new virtualenv using requirements.txt:
# cd to project root
# create virtualenv (this makes sure to use the virtualenv for python3):
virtualenv -p python3 <env_name>
# activate it
source <env_name>/bin/activate
# install requirements
pip install -r requirements/dev.txt