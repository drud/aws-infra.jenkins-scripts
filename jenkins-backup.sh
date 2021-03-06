#!/bin/bash -xe

if [ -d $JENKINS_HOME/.git ]; then
  cd $JENKINS_HOME
else
  cd $JENKINS_HOME
  git init
  git remote add origin git@github.com:drud/aws-infra.jenkins-backup.git
fi;

# Move into the jenkins directory
git fetch --all

#Add all top level xml files.
git add *.xml

# Add all job config.xml files.
git add -f jobs/*/config.xml
git add -f jobs/*/nextBuildNumber

# Add all user config.xml files.
git add users/*/config.xml

# Add all user content files.
git add userContent/*

git add fingerprints/*/*/*.xml

# Add plugins.
git add plugins/*.jpi

# Back-up the workspace directory
git add workspace/*/*.xml

# Capture known_hosts
git add .ssh/known_hosts

# Commit the differences
git status
git commit -a -m "Automated commit of jenkins chaos"
#git merge -s ours origin/master
git push origin master
# Remove files from the remote repo that have been removed locally.
# git log --pretty=format: --name-only --diff-filter=D
# COUNT=`git log --pretty=format: --name-only --diff-filter=D | wc -l`
# if [ $COUNT -ne 0 ]; then
#   git log --pretty=format: --name-only --diff-filter=D | xargs git rm -f
#   git commit -a -m "Automated removal of files."
# fi
#
# Push the commit up to the remote repository.
# git push origin master
