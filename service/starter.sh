#!/usr/bin/env bash
export DISPLAY=:0
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR=${DIR}/..
echo ${BASE_DIR}
cd ${BASE_DIR}
# reset your current branch (master) to origin's master
git checkout main
git pull
git reset --hard main
sudo /usr/local/bin/python3.12 -m pip install -r requirements.txt
export PYTHONPATH=${PYTHONPATH}:${BASE_DIR}
source /etc/environment
/usr/local/bin/python3.12 service/runner.py
export PYWIKIBOT_DIR=/home/pi/.pywikibot_protect/
/usr/local/bin/python3.12 service/protect.py
