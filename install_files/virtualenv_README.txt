# NOTE: before installing pygraphviz, run this command:
sudo apt-get install graphviz libgraphviz-dev pkg-config

#######################
to export the virtualenv:
pip freeze > requirements.txt

to create a new virtualenv using requirements.txt:
# cd to project root
virtualenv <env_name>
source <env_name>/bin/activate
pip install -r requirements.txt

