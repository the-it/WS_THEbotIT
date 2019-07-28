#!/bin/bash

set -x
sudo apt-get update
sudo apt-get install -y python-pip git
pip install ansible
ANSIBLE_REPO="ansible_roles"
if [ ! -d "$ANSIBLE_REPO" ] ; then
    git clone "https://github.com/the-it/$ANSIBLE_REPO.git"
fi
ansible-galaxy install -r "$ANSIBLE_REPO/requirements.yml"
