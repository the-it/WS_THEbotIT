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
sudo python3.7 -m pip install -r requirements.txt
export PYTHONPATH=${PYTHONPATH}:${BASE_DIR}
source /etc/environment
python3.7 scripts/runner.py
