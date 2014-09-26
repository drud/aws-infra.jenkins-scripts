#!/bin/bash -xe

export NMDCHEF_NODE_NAME=jenkins_ac
export NMDCHEF_CLIENT_KEY=/var/jenkins_home/.chef/chef_clientkey.pem
export NMDCHEF_VALIDATION_CLIENT_NAME=newmediadenver-validator
export NMDCHEF_VALIDATION_KEY=/var/jenkins_home/.chef/chef_validationkey.pem
export NMDCHEF_SERVER_URL=https://api.opscode.com/organizations/newmediadenver
export HOME=$WORKSPACE

env

git checkout packer-clean
git fetch --all
git pull
knife download /roles
knife download /data_bags
knife download /environments
rm -rf vendor/cookbooks/*
knife download /cookbooks
git config user.email "ops@newmediadenver.com"
git config user.name "Jenkins"
git config push.default simple
git remote -v
git branch
git status
git add .
git update-index -q --refresh
CHANGED=$(git diff-index --name-only HEAD --)
if [ ! -z "$CHANGED" ];
    then git commit -am "Jenkins $BUILD_ID $BUILD_TAG"
fi
git push
