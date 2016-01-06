#!/bin/bash

cd  /var/www/;
for dir in `ls` ;
do
  echo '----------------------------';
  echo "Analyzing $dir";
  a=0;
        b=0;
  # Get the current symlink so we can ignore it
  current=`readlink /var/www/$dir/current`;
  current=${current:9}
  echo "Current release: $current"
  for i in $(ls -t /var/www/$dir/releases --ignore='.[^.]' --ignore='$current');
  do
    a=`expr $a + 1`;
      if [[ $a -gt $1 ]]; then
        b=`expr $b + 1`;
        echo "Deleting: '/var/www/$dir/releases/$i";
        # rm -rf /var/www/$dir/releases/$i
      fi;
  done
        echo "Found $a release(s) that are not the current release. Deleted $b";
        echo '----------------------------';
done