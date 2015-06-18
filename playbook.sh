#!/bin/bash -xe
ansible-playbook -i /etc/ansible/hosts -vvvv $JENKINS_HOME/workspace/jenkins-ansible/hosts/$1.yml --private-key /var/jenkins_home/.ssh/aws.pem -u $3 --tags $2
