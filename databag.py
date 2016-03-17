# Find databags where production is percona01 or percona
import os,sys
import subprocess
import json
from pprint import pprint as p
import ast
import click
import tempfile

jenkins_home = os.getenv("JENKINS_HOME")
secret_file = "%s/.chef/nmd_encrypted_data_bag_secret" % (jenkins_home)

def construct_cmd(op, container, bag_name, json_tmp_file_name):
  cmd = "knife data bag %s %s %s" % (op, container, bag_name)
  secret = "--secret-file %s" % (secret_file)
  cmd = "%s %s -F json > %s" % (cmd, secret, json_tmp_file_name)
  return cmd

def run_cmd(op="show", container="nmdhosting", bag_name="", clean_up=True):
  json_tmp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
  json_tmp_file.close()
  # This will write out to a tmp json file
  subprocess.call(construct_cmd(op, container, bag_name, json_tmp_file.name), shell=True)
  # Pull that clean data back in
  with open(json_tmp_file.name) as data_file:    
    data = json.load(data_file)
  if clean_up:
    # I am not your mother...clean-up after yourself. :-)
    json_tmp_file.delete=True
  return data

def search_all(environment="_default", search_key="db_host", search_term=""):
  ignored_databags = []
  matches = {}
  container = "nmdhosting"
  all_clients = run_cmd(op="show", container=container, bag_name="")
  for bag_name in all_clients:
    print "Working on %s/%s" % (container, bag_name)
    site_bag = run_cmd(op="show", container=container, bag_name=bag_name)
    if unicode(environment) not in site_bag:
      print "ERROR: Environment '%s' not found for databag %s/%s.\nAvailable environments include: %s" % (environment, container, bag_name, ", ".join(site_bag.keys()))
      print "Ignoring databag %s/%s." % (container, bag_name)
      ignored_databags.append((container,bag_name))
      continue
    env_bag = site_bag[environment]
    if search_key not in env_bag:
      print "Key '%s' not found in %s/%s['%s']. Skipping..." % (search_key, container, bag_name, environment)
      continue
    if not search_term.lower() in env_bag[search_key].lower():
      print "Term '%s' not found in %s/%s['%s']['%s']" % (search_term, container, bag_name, environment, search_key)
      continue
    print "'%s' matches search of '%s' in %s/%s['%s']['%s']\n" % (env_bag[search_key], search_term, container, bag_name, environment, search_key)
    matches[bag_name] = site_bag
  return matches

def create_from_file(container, bag_name, json_tmp_file_name):
  secret = "--secret-file %s" % secret_file
  cmd = "knife data bag from file {0} '{1}' {2}".format(container, json_tmp_file_name, secret)
  subprocess.call(cmd, shell=True)

def change_value(bag_name, container="nmdhosting", environment="_default", key="db_host", term=""):
  print "%s/%s['%s']['%s']='%s'" % (container, bag_name, environment, key, term)
  old_bag = get_databag(bag_name, container)
  # And change the databag value to what we want
  old_bag[environment][key] = term

  save_databag(old_bag, bag_name, container)

def get_databag(bag_name, container="nmdhosting"):
  bag = run_cmd(op="show", container=container, bag_name=bag_name, clean_up=False)
  return bag

def save_databag(databag, bag_name, container="nmdhosting"):
  # Write the data to the file for consumption by the script
  tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
  tmp.write(json.dumps(databag))
  tmp.close()

  # And load the databag from this new file
  create_from_file(container, bag_name, tmp.name)
  tmp.delete=True
  


if __name__ == '__main__':
  # environment = "staging"
  # key = "db_host"
  # db_host = "percona"
  #search_all(environment=environment, search_key=key, search_term=db_host)
  # Make sure nmdhosting/test123456fsdlkjf exists
  change_value(bag_name="test123456fsdlkjf",
    container="nmdhosting",
    environment="staging",
    key="wonderful",
    term="people2")

