#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Example usage:
# python s3trim.py --count 14 --key=AKIAJXWDNYTONJLIGLYQ --secret=bELjuG3LfAAVT5pj1xmc5/6j8Ze8Yjn9fU9xquJK nmdarchive christest/production

import argparse
import logging
import operator
import re
from collections import OrderedDict as Dict
from boto.s3.connection import S3Connection

debug = True

parser = argparse.ArgumentParser(description="Get the key for the latest S3 Object matching a prefix.", prog="s3trim")
parser.add_argument("bucket", help="S3 bucket.")
parser.add_argument("prefix", help="S3 Object key prefix.")
parser.add_argument("-c", "--count", help="Number of files to leave.", dest='aws_bucket_count')
parser.add_argument("-k", "--key", help="Your amazon access key.", dest='aws_access_key')
parser.add_argument("-sk", "--secret", help="Your amazon secret key.", dest='aws_secret_key')
parser.add_argument("-l", "--log", help="Sets the log level. Defaults to INFO.", default='INFO')

def main(bucket, prefix, aws_access_key='', aws_secret_key='', log='info', aws_bucket_count=5):
    global aws_key
    aws_key = aws_access_key

    global aws_secret
    aws_secret = aws_secret_key

    s3 = S3Connection(aws_key, aws_secret)
    bucket = s3.get_bucket(bucket)

    sorted_results = get_results(bucket)
    
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
      #if timestamp not in results[env][bag]:
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