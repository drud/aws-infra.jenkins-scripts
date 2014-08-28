#!/bin/bash -xe

export CHEF_VALIDATION_KEY=/var/jenkins_home/.chef/chef_validationkey.pem
export CHEF_VALIDATION_CLIENT_NAME=newmediadenver-validator
export CHEF_CLIENT_KEY=/var/jenkins_home/.chef/chef_clientkey.pem
export CHEF_NODE_NAME=jenkins_ac
export CHEF_SERVER_URL=https://api.opscode.com/organizations/newmediadenver
if [ -z "$COOKBOOK_NAME" ]; then
  export COOKBOOK_NAME="nmd$JOB_NAME"
fi
env

case "$GIT_BRANCH" in
  'origin/master')
    CHEF_ENVIRONMENT='production'
    ;;
  'origin/staging')
    CHEF_ENVIRONMENT='staging'
    ;;
  *)
    CHEF_ENVIRONMENT='_default'
    ;;
esac

knife exec -E "nodes.find('chef_environment:$CHEF_ENVIRONMENT AND $COOKBOOK_NAME:action') { |n| n.normal.$COOKBOOK_NAME.action = '$CHEF_ACTION'; n.save}"
knife ssh -A "chef_environment:$CHEF_ENVIRONMENT AND $COOKBOOK_NAME:action" "sudo chef-client" --ssh-user jenkins_ac
