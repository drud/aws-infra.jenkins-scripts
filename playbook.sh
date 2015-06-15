#!/bin/bash -xe
ansible-playbook -i /etc/ansible/hosts -vvvv $WORKSPACE/$1.yml --private-key /var/jenkins_home/.ssh/aws.pem -u root