#!/bin/bash -xe
ansible-playbook -e "drud_jumpcloud_client_id=$DRUD_JUMPCLOUD_CLIENT_ID" -i /etc/ansible/hosts -vvvv $JENKINS_HOME/workspace/jenkins-ansible/hosts/$1.yml --private-key /var/jenkins_home/.ssh/aws.pem -u $3 --tags $2
