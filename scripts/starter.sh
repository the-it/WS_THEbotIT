#!/bin/sh
export DISPLAY=:0
cd /home/pi/WS_THEbotIT/scripts/
git pull
python3 -O runner.py
