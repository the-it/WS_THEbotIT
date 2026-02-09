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
rm -rf service/ws_re/register/data
sudo /usr/local/bin/python3 -m pip install --user uv
uv sync
export PYTHONPATH=${PYTHONPATH}:${BASE_DIR}
source /etc/profile
uv run service/runner.py
export PYWIKIBOT_DIR=/home/pi/.pywikibot_protect/
uv run service/protect.py
