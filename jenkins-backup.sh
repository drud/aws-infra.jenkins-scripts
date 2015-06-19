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
git checkout 'users/root@292261-web5.www.travelagentcentral.com/config.xml'
#Add all top level xml files.
git add *.xml

# Add all job config.xml files.
git add jobs/*/config.xml
git add -f jobs/*/nextBuildNumber

# Add all user config.xml files.
git add users/*/config.xml

# Add all user content files.
git add userContent/*

# Add plugins.
git add plugins/*.hpi

# Remove files from the remote repo that have been removed locally.
COUNT=`git log --pretty=format: --name-only --diff-filter=D | wc -l`
if [ $COUNT -ne 0 ]
  then git log --pretty=format: --name-only --diff-filter=D | xargs git rm
fi

# Commit the differences
git commit -a -m "Automated commit of jenkins chaos"

git fetch --all

git rebase origin/master

# Push the commit up to the remote repository.
git push origin master