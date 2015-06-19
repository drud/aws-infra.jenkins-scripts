#!/bin/bash -xe
env

if [ -d $JENKINS_HOME/.git ]; then
  cd $JENKINS_HOME
  git status
else
  cd $JENKINS_HOME
  git init
  git remote add origin git@github.com:newmediadenver/jenkins.git
fi;

# Move into the jenkins directory
cd $JENKINS_HOME
git fetch --all
git rebase origin/master