#!/bin/bash -xe

env

ssh -i /var/jenkins_home/.ssh/id_rsa jenkins_ac@stagingweb001.nmdev.us "sudo -E -P /home/jenkins_ac/scripts/current/site-archive-child.sh $SITE"
scp -i /var/jenkins_home/.ssh/id_rsa jenkins_ac@stagingweb001.nmdev.us:/tmp/$SITE.tar.gz .
