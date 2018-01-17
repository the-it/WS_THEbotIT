#!/usr/bin/env sh

echo normal unit tests
python -m unittest
echo coverage
coverage run tests.py
echo pycodestyle
pep8
echo flake8
flake8 --exit-zero