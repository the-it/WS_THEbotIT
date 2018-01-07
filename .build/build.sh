#!/usr/bin/env sh

python -m unittest
echo pycodestyle
pep8
echo flake8
flake8 --exit-zero