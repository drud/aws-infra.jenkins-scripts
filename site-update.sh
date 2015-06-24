#!/bin/bash -xe
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

knife exec -E "nodes.find('chef_environment:$CHEF_ENVIRONMENT AND $COOKBOOK_NAME:action') { |n| n.normal.$COOKBOOK_NAME.action = '$CHEF_ACTION'; n.save}" --verbose --config /var/jenkins_home/workspace/jenkins-chef-client/.chef/knife.rb
PRIVATEIP=$(knife search node "chef_environment:$CHEF_ENVIRONMENT AND $COOKBOOK_NAME:action" -c ${JENKINS_HOME}/workspace/jenkins-scripts/.chef/knife.rb | sed -n '4p' | awk '{print $2}')
ssh -A -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP 'chef-client -l debug'
knife exec -E "nodes.find('chef_environment:$CHEF_ENVIRONMENT AND $COOKBOOK_NAME:action') { |n| n.normal.$COOKBOOK_NAME.action = 'sleep'; n.save}" --verbose --config /var/jenkins_home/workspace/jenkins-chef-client/.chef/knife.rb
