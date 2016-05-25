#!/bin/bash
if [ -z "$1" -o -z "$2" -o -z "$3" ]; then
  echo "This script requires that you pass in the path to a webroot and the sha to compare to run."
  echo "Usage: ./check-sha WEBROOT GOODSHA"
  exit 1;
fi

SHA=$(git --git-dir=$WEBROOT/.git rev-parse HEAD)
if [ "$SHA" != "$GOODSHA" ]; then
  echo "NO MATCH"
else
  echo "MATCH"
fi