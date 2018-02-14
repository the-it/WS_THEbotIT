#!/usr/bin/env sh

echo "########## PYCODESTYLE #########"
pep8
echo "############ FLAKE8 ############"
flake8 --exit-zero
export PYWIKIBOT2_NO_USER_CONFIG=1
echo "########### COVERAGE ###########"
coverage run test/all_test.py