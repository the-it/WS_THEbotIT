#!/bin/sh
export DISPLAY=:0
cd /home/pi/WS_THEbotIT/
git pull
pip3 install -r requirements.txt
cd scripts/
python3 runner.py
