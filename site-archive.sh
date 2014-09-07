#!/bin/bash -xe

export CHEF_VALIDATION_KEY=/var/jenkins_home/.chef/chef_validationkey.pem
export CHEF_VALIDATION_CLIENT_NAME=newmediadenver-validator
export CHEF_CLIENT_KEY=/var/jenkins_home/.chef/chef_clientkey.pem
export CHEF_NODE_NAME=jenkins_ac
export CHEF_SERVER_URL=https://api.opscode.com/organizations/newmediadenver
if [ -z "$COOKBOOK_NAME" ]; then
  export COOKBOOK_NAME="nmd$SITE"
fi
env
CHEF_ENVIRONMENT='staging'
knife ssh -A "chef_environment:$CHEF_ENVIRONMENT AND $COOKBOOK_NAME:action" "sudo -E -P /home/jenkins_ac/scripts/current/site-archive-child.sh" --ssh-user jenkins_ac
