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
uv sync
export PYTHONPATH=${PYTHONPATH}:${BASE_DIR}
source /etc/profile
# /etc/profile overwrites PATH, re-add uv's install dir
export PATH="$HOME/.local/bin:$PATH"
uv run service/runner.py
export PYWIKIBOT_DIR=/home/pi/.pywikibot_protect/
uv run service/protect.py
