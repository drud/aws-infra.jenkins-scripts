#!/bin/bash -x
env

if [ -d $JENKINS_HOME/.git ]; then
  cd $JENKINS_HOME
  git status
else
  cd $JENKINS_HOME
  git init
  git remote add origin git@bitbucket.org:hdscode/jenkins.git
fi;

# Move into the jenkins directory
cd $JENKINS_HOME

#Add all top level xml files.
git add *.xml

# Add all job config.xml files.
git add jobs/*/config.xml

# Add all user config.xml files.
git add users/*/config.xml

# Add all user content files.
git add userContent/*

# Remove files from the remote repo that have been removed locally.
COUNT=`git log --pretty=format: --name-only --diff-filter=D | wc -l`
if [ $COUNT -ne 0 ]
  then git log --pretty=format: --name-only --diff-filter=D | xargs git rm
fi

# Commit the differences
git commit -a -m "Automated commit of jenkins chaos"

# Push the commit up to the remote repository.
git push origin master