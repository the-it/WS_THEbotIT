#!/bin/bash

set -x
sudo apt-get update
sudo apt-get install -y python-pip git
sudo pip install ansible
ANSIBLE_REPO="ansible_roles"
if [ ! -d "$ANSIBLE_REPO" ] ; then
    git clone "https://github.com/the-it/$ANSIBLE_REPO.git"
fi
ansible-galaxy install -r "$ANSIBLE_REPO/requirements.yml"
if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    exit 1
  else
  ANSIBLE_ROLL=$1
fi
ansible-playbook "$ANSIBLE_REPO/$ANSIBLE_ROLL.yml"
rm -rf $ANSIBLE_REPO
set +x
