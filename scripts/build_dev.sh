#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${DIR}
cd ..  # we are at the project's root
pip install -r requirements/dev.txt
python paguen_po/manage.py migrate
yarn
python paguen_po/manage.py collectstatic_js_reverse
yarn run build