#!/bin/bash

. ./openrc.sh; ansible-playbook -i hosts -u ubuntu --key-file=~/.ssh/amclo --ask-become-pass twitter_jam.yaml -e "ansible_python_interpreter=/usr/bin/python3"