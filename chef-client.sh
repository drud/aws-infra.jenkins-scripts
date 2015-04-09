#!/bin/bash -xe
PRIVATEIP=$(knife search node "name:$HOSTNAME" | sed -n '6p' | awk '{print $2}')
ssh -p$PORT -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP 'chef-client -l debug'
