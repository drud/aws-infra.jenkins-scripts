#!/usr/bin/python
import databag
import click
import sys
import hvac
import os
import requests.packages.urllib3

debug=False
file_name = "vault_token.txt"

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
@click.option('--url', prompt="What is the URL of the server you are trying to add?", help="URL of server you're trying to add")
@click.option('--environment', prompt="Which environment?", help="'staging' or 'production'", type=click.Choice(['staging', 'production']))
#@click.option('--add/--remove', default="add", help="'add' or 'remove' the entry")
@click.option('--add', 'operation', flag_value='add', default=True, help="Add this entry to the proxy bag")
@click.option('--remove', 'operation', flag_value='remove', help="Remove this entry from the proxy bag")
@click.option('--auth', default=False, is_flag=True, help="Adds an auth screen")
@click.option('--www-force', default=False, is_flag=True, help="Forces the url to rewrite to www.*")
@click.option('--ssl-force', default=False, is_flag=True, help="Force a rewrite to https")
@click.option('--ssl', default=None, help="String that lines up with the SSL entry in the auth databag")
def site_proxy_entry(url, environment, operation, auth, www_force, ssl_force, ssl):
  """
  Add or remove entries from a proxy-structured datBabag.
  """
  vault_client = get_vault_client()
  proxy_databag = vault_client.read("secret/databags/nmdproxy/upstream")['data']
  if environment=='production':
    site_entries = proxy_databag[environment]['webcluster01']['apps']
  elif environment=="staging":
    site_entries = proxy_databag[environment]['web01']['apps']
  else:
    raise Exception("Unrecognized environment of '{environment}. Available options are 'production' and 'development'".format(environment=environment))
    sys.exit(1)

  if operation == "add":
    site_entries[url] = {}
    if auth:
      site_entries[url]["auth"] = True
    if www_force:
      site_entries[url]["www_force"] = True
    if ssl:
      site_entries[url]["ssl"] = ssl
    if ssl_force:
      site_entries[url]["ssl_force"] = True
  elif operation == "remove":
    if url in site_entries.keys():
      site_entries.pop(url)
  else:
    print "Unrecognized operation of '{operation}'".format(operation=operation)

  # Put it all back together
  if environment=='production':
    proxy_databag[environment]['webcluster01']['apps'] = site_entries
  elif environment=="staging":
    proxy_databag[environment]['web01']['apps'] = site_entries

  vault_client.write('secret/databags/nmdproxy/upstream', **proxy_databag)

if __name__ == '__main__':
    site_proxy_entry()
