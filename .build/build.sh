#!/usr/bin/env sh

echo "########### COVERAGE ###########"
coverage run test/all_test.py
echo "########## PYCODESTYLE #########"
pep8
echo "############ FLAKE8 ############"
flake8 --exit-zero