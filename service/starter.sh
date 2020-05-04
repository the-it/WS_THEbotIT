#!/usr/bin/env bash
export DISPLAY=:0
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR=${DIR}/..
echo ${BASE_DIR}
cd ${BASE_DIR}
# reset your current branch (master) to origin's master
git checkout master
git pull
git reset --hard master
sudo /usr/local/bin/python3.8 -m pip install -r requirements.txt
export PYTHONPATH=${PYTHONPATH}:${BASE_DIR}
source /etc/environment
/usr/local/bin/python3.8 service/runner.py