#!/bin/bash -xe

export CHEF_VALIDATION_KEY=/var/jenkins_home/.chef/chef_validationkey.pem
export CHEF_VALIDATION_CLIENT_NAME=newmediadenver-validator
export CHEF_CLIENT_KEY=/var/jenkins_home/.chef/chef_clientkey.pem
export CHEF_NODE_NAME=jenkins_ac
export CHEF_SERVER_URL=https://api.opscode.com/organizations/newmediadenver

knife ssh -A "name:$HOSTNAME" "sudo -E -P chef-client" --ssh-user jenkins_ac -a ipaddress -i /var/jenkins_home/.ssh/id_rsa
