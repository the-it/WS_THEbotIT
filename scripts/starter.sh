#!/usr/bin/env bash
export DISPLAY=:0
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR=$DIR/..
echo $BASE_DIR
cd $BASE_DIR
# reset your current branch (master) to origin's master
git checkout master
git pull
git reset --hard master
sudo pip3 install -r requirements.txt
export PYTHONPATH=$PYTHONPATH:$BASE_DIR
python3 scripts/runner.py