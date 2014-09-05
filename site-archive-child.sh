#!/bin/bash

# Estimate necessary disk space
current_size=`du -s /var/www/$site | cut -f1`
current_available=`df | grep /dev/xvda | awk -F ' ' '{print $4}'`
current_buffer=500000
remaining=$(expr $current_available - $current_size)

if [ $remaining -gt $current_buffer ];then
  drush @$1 archive-dump --destination=/tmp/$1.tar.gz --overwrite
  chown jenkins_ac:jenkins_ac /tmp/$1.tar.gz
else
  echo "Insufficient disk space on the host to take a drush archive-dump."
  exit 1
fi
