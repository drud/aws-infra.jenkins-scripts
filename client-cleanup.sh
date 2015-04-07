#!/bin/bash -xe
PRIVATEIP=$(knife search node "name:$HOSTNAME" | sed -n '6p' | awk '{print $2}')
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP 'rm -rf /root/.drush && rm -rf /tmp/* && rm -rf /var/chef/cache/*.tar.gz'
