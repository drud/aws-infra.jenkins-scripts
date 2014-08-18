#!/bin/bash -xe

export CHEF_VALIDATION_KEY=/var/jenkins_home/.chef/chef_validationkey.pem
export CHEF_VALIDATION_CLIENT_NAME=newmediadenver-validator
export CHEF_CLIENT_KEY=/var/jenkins_home/.chef/chef_clientkey.pem
export CHEF_NODE_NAME=jenkins_ac
export CHEF_SERVER_URL=https://api.opscode.com/organizations/newmediadenver
export COOKBOOK_NAME="nmd$JOB_NAME"

env

knife exec -E "nodes.find('$COOKBOOK_NAME:action') { |n| n.normal.$COOKBOOK_NAME.action = 'update'; n.save}"
knife ssh -A "$COOKBOOK_NAME:action" "sudo chef-client" --ssh-user jenkins_ac
