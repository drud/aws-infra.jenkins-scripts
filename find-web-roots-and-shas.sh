#!/bin/bash

ROOTS_AND_SHAS=$(find /var/www -maxdepth 2 -type l -name current -print -exec git --git-dir={}/.git rev-parse HEAD \;)
echo $ROOTS_AND_SHAS