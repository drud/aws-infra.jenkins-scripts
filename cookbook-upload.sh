#!/bin/bash -xe

export CHEF_VALIDATION_KEY=/var/jenkins_home/.chef/chef_validationkey.pem
export CHEF_VALIDATION_CLIENT_NAME=newmediadenver-validator
export CHEF_CLIENT_KEY=/var/jenkins_home/.chef/chef_clientkey.pem
export CHEF_NODE_NAME=jenkins_ac
export CHEF_SERVER_URL=https://api.opscode.com/organizations/newmediadenver
env
COOKBOK_NAME=`awk '$1=="name"{print $2}' $WORKSPACE/metadata.rb | sed "s/'//g"`

knife cookbook upload $COOKBOK_NAME -o $JENKINS_HOME/workspace --verbose
