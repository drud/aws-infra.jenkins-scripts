#!/usr/bin/python
# Find databags where production is percona01 or percona
import os,sys
import subprocess
import json
from pprint import pprint as p
import ast
import tempfile
import click
import ast

jenkins_home = str(os.getenv("JENKINS_HOME"))
secret_file = os.getenv('NMDCHEF_SECRET_FILE')
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
local = True if "/var/jenkins_home" not in jenkins_home else False

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='1.0.0')
def siteman():
  pass

def construct_cmd(op, container, bag_name, json_tmp_file_name):
  """
  Assemble the command string

  :param op: 'show', 'edit', 'create', 'delete', 'from file', 'list'
  :param container: 'nmdhosting', 'nmdtest', 'nmdproxy'
  :param bag_name: The name of the datbad e.g. 'upstream'
  :param json_tmp_file_name: Path to the *.json tmp file for databag tmp storage

  :returns string command
  """
  cmd=""
  if local:
    cmd += "cd ~/cookbooks/chef; bundle exec"
  cmd += " knife data bag {op} {container} {bag_name}".format(op=op, container=container, bag_name=bag_name)
  cmd += " --secret-file {secret}".format(secret=secret_file)
  if not local:
    cmd += " -c /var/jenkins_home/workspace/jenkins-scripts/.chef/knife.rb"
  cmd += " -F json > {json_file}".format(json_file=json_tmp_file_name)
  if local:
    cmd += "; cd -;"
  return cmd

def run_cmd(op="show", container="nmdhosting", bag_name="", clean_up=True):
  """
  Calls construct_cmd(), runs that command, and then sucks it into memory

  :param op: 'show', 'edit', 'create', 'delete', 'from file', 'list'
  :param container: 'nmdhosting', 'nmdtest', 'nmdproxy'
  :param bag_name: The name of the databag e.g. 'upstream'
  :param clean_up: Specifies whether or not to delete the tmp file

  :returns dict databag
  """
  json_tmp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
  json_tmp_file.close()
  # This will write out to a tmp json file
  subprocess.call(construct_cmd(op, container, bag_name, json_tmp_file.name), shell=True)
  # Pull that clean data back in
  with open(json_tmp_file.name) as data_file:    
    data = json.load(data_file)
    if clean_up:
      # I am not your mother...clean-up after yourself. :-)
      #os.remove(json_tmp_file.name)
      json_tmp_file.delete=True
  return data

def search_all(container, environment="_default", search_key="db_host", search_term=""):
  """
  Searches all databags within a container for a term. This is useful if you are trying to find all databags that have been marked inactive, or databags that are on a certain db server.

  :param container: Container to search e.g. 'nmdhosting', 'nmdtest', 'nmdproxy'
  :param environment: Environment to search in the container e.g. "_default", "production", "staging"
  :param search_key: The name of the search term e.g. db_name
  :param search_term: The term you are searching for e.g. percona

  :returns dict matching databags
  """
  ignored_databags = []
  matches = {}
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
    if type(search_term) == type(str) and type(search_key) == type(str) and not search_term.lower() in env_bag[search_key].lower():
      print "Term '%s' not found in %s/%s['%s']['%s']" % (search_term, container, bag_name, environment, search_key)
      continue
    print "'%s' matches search of '%s' in %s/%s['%s']['%s']\n" % (env_bag[search_key], search_term, container, bag_name, environment, search_key)
    matches[bag_name] = site_bag
  return matches

def create_from_file(container, bag_name, json_tmp_file_name):
  """
  Creates a databag from a json file

  :param container: Container to target e.g. 'nmdhosting', 'nmdtest', 'nmdproxy'
  :param bag_name: Name of the bag you want to create/overwrite
  :param json_tmp_file_name: Path to the .json file

  :returns string result of the call to shell
  """
  cmd=""
  if local:
    cmd += "cd ~/cookbooks/chef; bundle exec"
  cmd += " knife data bag from file {0} '{1}'".format(container, json_tmp_file_name)
  cmd += " --secret-file {secret}".format(secret=secret_file)
  if not local:
    cmd += " -c /var/jenkins_home/workspace/jenkins-scripts/.chef/knife.rb"
  if local:
    cmd += "; cd -;"
  return subprocess.call(cmd, shell=True)

def change_value(bag_name, container="nmdhosting", environment="_default", key="db_host", term=""):
  """
  Changes a value in a databag.

  :param bag_name: The name of the databag to target
  :param container: Container to target e.g. 'nmdhosting', 'nmdtest', 'nmdproxy'
  :param environment: Environment to target in the container e.g. "_default", "production", "staging"
  :param key: The name of the value you want to create/overwrite
  :param term: The new value you want to create/overwrite

  :returns string result of the call to shell
  """
  print "%s/%s['%s']['%s']='%s'" % (container, bag_name, environment, key, term)
  old_bag = get_databag(bag_name, container)
  # And change the databag value to what we want
  old_bag[environment][key] = term

  save_databag(old_bag, bag_name, container)

def get_databag(bag_name, container="nmdhosting"):
  """
  Fetches a standard databag

  :param bag_name: The name of the databag to fetch
  :param container: Container the databag was in - e.g. 'nmdhosting', 'nmdtest', 'nmdproxy'

  :returns dict databag
  """
  bag = run_cmd(op="show", container=container, bag_name=bag_name, clean_up=False)
  return bag

def save_databag(databag, bag_name, container="nmdhosting"):
  """
  Overwrites an existing databag

  :param databag: The dict representation of the databag 
  :param bag_name: The name of the bag to overwrite e.g. 'newmediadenver', 'upstream'
  :param container: Container of the databag e.g. 'nmdhosting', 'nmdtest', 'nmdproxy'

  :returns True if sucessful completion
  """
  # Write the data to the file for consumption by the script
  tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
  tmp.write(json.dumps(databag))
  tmp.close()

  # And load the databag from this new file
  create_from_file(container, bag_name, tmp.name)
  tmp.delete=True
  os.remove(tmp.name)
  return True

@siteman.command()
@click.option('--environment', help="Ex) staging", type=click.Choice(['_default', 'staging', 'production']))
@click.option('--key', help="Ex) db_host")
@click.option('--term', help="Ex) A quoted string that corresponds to a pythonic data structure ['web01.newmediadenver.com','web02.newmediadenver.com']")
@click.option('--new-term', help="Ex) ['web02.newmediadenver.com','web03.newmediadenver.com']")
def find_and_replace(environment="staging", key="db_host", term="fake_db", new_term="real_db"):
  # Try to evaluate the terms safely into pythonic equivalents
  try:
    if "[" in term or "{" in term:
      term = ast.literal_eval(term)
    if "[" in new_term or "{" in new_term:
      new_term = ast.literal_eval(new_term)
  except ValueError as e:
    print "One of your terms is in an unrecognized format."
  for bag_name, bag in search_all(container="nmdhosting", environment=environment, search_key=key, search_term=term).items():
    print "Working on {bag_id}".format(bag_id=bag['id'])
    change_value(bag_name=bag['id'],
      container="nmdhosting",
      environment=environment,
      key=key,
      term=new_term)

if __name__ == '__main__':
  siteman()

