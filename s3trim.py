#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Example usage:
# python s3trim.py --count 14 --key=AWS_KEY --secret=AWS_SECRET_KEY nmdarchive christest/production

import argparse
import logging
import operator
import re
import time
from collections import OrderedDict as Dict
from boto.s3.connection import S3Connection
import sys

debug = False

parser = argparse.ArgumentParser(description="Prune all files in S3. Note: Staging and _Default environments will only retain a single back-up.", prog="s3trim")
parser.add_argument("bucket", help="S3 bucket.")
parser.add_argument("-c", "--count", help="Number of days of files to leave in production.", dest='aws_bucket_count')
parser.add_argument("-k", "--key", help="Your amazon access key.", dest='aws_access_key')
parser.add_argument("-sk", "--secret", help="Your amazon secret key.", dest='aws_secret_key')
parser.add_argument("-l", "--log", help="Sets the log level. Defaults to INFO.", default='INFO')
def main(bucket, aws_access_key='', aws_secret_key='', log='info', aws_bucket_count=5):
    global aws_key
    aws_key = aws_access_key

    global aws_secret
    aws_secret = aws_secret_key

    s3 = S3Connection(aws_key, aws_secret)
    bucket = s3.get_bucket(bucket)

    sorted_results = get_results(bucket)

    trim_by_day(bucket, sorted_results, aws_bucket_count)
    #trim_by_count(bucket, sorted_results)
    

def trim_by_count(bucket, sorted_results):
    for env, bags in sorted_results.items():
      logger.info("Working on the {env} environment.".format(env=env))
      for name, bag in bags.items():
        logger.info("Working on the {name} bag.".format(name=name))
        if env in ['_default', 'staging']:
          logger.info("This is a {env} environment, overriding retention to a single back-up.".format(env=env))
          removal_count = len(bag) - 1
        else:
          removal_count = len(bag) - int(aws_bucket_count)
        count = 0
        for timestamp, file_name in bag:
          if count >= removal_count:
            logger.info("Previous file count: {count}".format(count=len(bag)))
            logger.info("Removed files: {total}".format(total=count))
            logger.info("New file count: {count}".format(count=(len(bag)-count)))
            logger.info("")
            break
          count+=1
          if not debug:
            bucket.delete_key(file_name)
          logger.info("Removed %s" % (file_name))
      

# Retain 2 weeks of S3 data in prod and the most recent back-up in staging and sefault
def trim_by_day(bucket,sorted_results,aws_bucket_count):
    now = int(time.time())
    num_days = aws_bucket_count
    num_secs = int(num_days) * 24 * 60 * 60
    oldest_timestamp = int(now - num_secs)
    total_removed_files = 0
    total_files = 0
    #counts = {e:0 for e in sorted_results.keys()}
    
    for env, bags in sorted_results.items():
      logger.info("Working on the {env} environment.".format(env=env))

      for name, bag in bags.items():
        logger.info("Working on the {name} bag.".format(name=name))
        
        # Setup the counters
        if env in ['_default', 'staging']:
          logger.info("This is a {env} environment, overriding retention to a single back-up.".format(env=env))
          removal_count = len(bag) - 1
        else:
          removal_count = len(bag) - int(aws_bucket_count) # Set a boundary in case there's less backups than days
        count = 0

        if len(bag) == 1:
          continue
        for timestamp, file_name in bag:
          # If the timestamp on the file is older than our limit
          # Majority of cases will fall here
          if int(timestamp) < oldest_timestamp:
            # If there's only our removal count left, bail, keep these always always
            if count >= removal_count:
              break
            count+=1
            if not debug:
              bucket.delete_key(file_name)
            logger.info("Removed %s" % (file_name))
            continue

          # If we've got an entry from a non-prod env, we need to wipe out all but 1
          if env in ['_default', 'staging'] and count < removal_count:
            count+=1
            if not debug:
              bucket.delete_key(file_name)
            logger.info("S Removed %s" % (file_name))
            continue
        total_removed_files+=count
        total_files+=len(bag)
        logger.info("Previous file count: {count}".format(count=len(bag)))
        logger.info("Removed files: {total}".format(total=count))
        logger.info("New file count: {count}".format(count=(len(bag)-count)))
        logger.info("")
        if len(bag)-count <= 0:
          logger.error("There were 0 files remaining on this removal. Something went wrong here. Bailing.")
          sys.exit(1)
    logger.info("Previous total file count: %d" % total_files)
    logger.info("Total removed files: %d" % total_removed_files)
    logger.info("New total file count: %d" % (total_files-total_removed_files))


def get_results(bucket):
    # christest/production-christest-1474858852.tar.gz
    # bag/env-bag-time.tar.gz
    #bucket_list = bucket.list(prefix)
    bucket_list = bucket.list()
    logger.info("Pulled file list from nmdarchive")

    structured_list = {}


    pattern = '(?P<bag>[a-zA-Z0-9]+)/(?P<env>[a-zA-Z0-9]+)-(?P<bag2>[a-zA-Z0-9]+)-(?P<timestamp>\d+)\.tar\.gz'
    regex = re.compile(pattern)
    results = {}
    count = 0
    logger.info("Scanning for valid archive files... (This will take a while).")
    for item in bucket_list:
      match = regex.match(item.name)
      if not match:
        continue
      bag = match.group('bag')
      env = match.group('env')
      bag2 = match.group('bag2')
      timestamp = match.group('timestamp')
      # Sanity check to make sure that the bags match
      if bag != bag2:
        logger.info("It looks like {name} is a malformed back-up entry. Consider deleting.".format(name=item))
        continue
      if env not in results:
        results[env] = {}
      if bag not in results[env]:
        results[env][bag] = {}
      results[env][bag][timestamp] = item

    sorted_results = {e: {b: Dict() for b in results[e].keys()} for e in results.keys()}
    for env, bags in results.items():
      for name, bag in bags.items():
        # Sort by timestamp
        sorted_results[env][name] = sorted(bag.items(), key=operator.itemgetter(1))

    # Now that everything is sorted, the first items are the oldest and the last items are newest
    return sorted_results


if __name__ == "__main__":
  args = parser.parse_args()
  logging.basicConfig(filename='s3trim_dryrun.log',level=logging.INFO)
  logger = logging.getLogger()
  exec("logger.setLevel(logging." + args.log.upper() + ")")

  handler = logging.StreamHandler()
  exec("handler.setLevel(logging." + args.log.upper() + ")")
  formatter = logging.Formatter("[%(levelname)s %(filename)s:%(lineno)s %(funcName)s()] %(message)s")
  handler.setFormatter(formatter)
  logger.addHandler(handler)

  arg_dict = vars(args)
  logging.debug("CLI args: %s" % args)
  main(**arg_dict)
