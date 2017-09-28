#!/bin/sh
export DISPLAY=:0
cd /home/pi/WS_THEbotIT/
# fetch from the default remote, origin
git fetch
# reset your current branch (master) to origin's master
git reset --hard origin/master
sudo pip3 install -r requirements.txt
cd scripts
python3 runner.py
