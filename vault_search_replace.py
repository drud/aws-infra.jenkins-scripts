#!/usr/bin/python
# Mass find/replace values in vault secrets in nmdhosting
import os,sys
import subprocess
import json
from pprint import pprint as p
import ast
import click
import ast
import requests
import hvac


# CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
file_name = "vault_token.txt"

# @click.group(context_settings=CONTEXT_SETTINGS)
# @click.version_option(version='1.0.0')
# def siteman():
#   pass

def get_vault_client():
    """
    Return a vault client if possible.
    """
    # Disable warnings for the insecure calls
    requests.packages.urllib3.disable_warnings()
    token_type = "GITHUB|SANCTUARY"
    vault_addr = os.getenv("VAULT_ADDR", "https://sanctuary.drud.io:8200")
    sanctuary_token_path = os.path.join('/var/jenkins_home/workspace/ops-create-sanctuary-token/', file_name)
    if os.path.exists(sanctuary_token_path):
        with open(sanctuary_token_path, 'r') as fp:
            vault_token = fp.read()
            token_type = "SANCTUARY"
    else:
        vault_token = os.getenv("GITHUB_TOKEN")
        token_type = "GITHUB"

    if not vault_addr or not vault_token:
        print "You must provide a GITHUB_TOKEN environment variables."
        print "(Have you authenticated with drud using `drud auth github` to create your GITHUB_TOKEN?)"
        sys.exit(1)

    if token_type == "SANCTUARY":
        vault_client = hvac.Client(url=vault_addr, token=vault_token, verify=False)
    elif token_type == "GITHUB":
        vault_client = hvac.Client(url=vault_addr, verify=False)
        vault_client.auth_github(vault_token)
    else: # The token value was not overridden
        print "Something went wrong."
        sys.exit(1)

    if vault_client.is_initialized() and vault_client.is_sealed():
        print "Vault is initialized but sealed."
        sys.exit(1)

    if not vault_client.is_authenticated():
        print "Could not get auth."
        sys.exit(1)

    print "Using {t_type} for authentication.".format(t_type=token_type.lower())
    return vault_client

@click.command()
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

  print "Searching for '{term}' in databags/nmdhosting/* and replacing matches with '{new_term}'".format(term=term, new_term=new_term)
  vault = get_vault_client()
  for site in vault.list('secret/databags/nmdhosting')['data']['keys']:
    site_data = vault.read("secret/databags/nmdhosting/{site}".format(site=site))['data']
    if key in site_data[environment] and site_data[environment][key] == term:
      print "Match in {site}[{env}][{key}]".format(site=site,env=environment, key=key)
      site_data[environment][key] = new_term
    else:
      print "No match"
    
    vault.write("secret/databags/nmdhosting/{site}".format(site=site), **site_data)

if __name__ == '__main__':
  find_and_replace()