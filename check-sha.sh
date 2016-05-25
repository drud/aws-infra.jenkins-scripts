#!/bin/bash
if [ -z "$1" -o -z "$2" ]; then
  echo "This script requires that you pass in the path to a webroot and the sha to compare to run."
  echo "Usage: ./check-sha WEBROOT GOODSHA"
  exit 1;
fi
WEBROOT=$1
GOODSHA=$2

SHA=$(git --git-dir=$WEBROOT/.git rev-parse HEAD)
if [ "$SHA" != "$GOODSHA" ]; then
  echo "$SHA NO"
else
  echo "$SHA MATCH"
fi