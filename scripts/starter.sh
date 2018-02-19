#!/usr/bin/env bash
export DISPLAY=:0
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR=$DIR/..
cd $BASE_DIR
# fetch from the default remote, origin
git fetch
# reset your current branch (master) to origin's master
git reset --hard origin/master
sudo pip3 install -r requirements.txt
python3 scripts/runner.py
