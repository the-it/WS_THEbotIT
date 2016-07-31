#!/bin/sh
export DISPLAY=:0
cd /home/pi/WS_THEbotIT/scripts/
ln -s ../externals/pywikibot/pywikibot ../pywikibot
git pull
python3 -O runner.py
