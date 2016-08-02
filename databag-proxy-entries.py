#!/usr/bin/python
import databag
import click
import sys
import hvac

debug=False

proxy_container="nmdproxy"
if debug:
  proxy_container="nmdtest"

def get_vault_client():
    vault_token = os.environ.get('GITHUB_TOKEN', "NO TOKEN FOUND") if 'GITHUB_TOKEN' in os.environ else os.environ.get('VAULT_TOKEN', "NO TOKEN FOUND")
    if vault_token == "NO TOKEN FOUND":
        print "Could not find GITHUB_TOKEN or VAULT_TOKEN in your environment. Have you run `drud secret auth`?"
        sys.exit(1)
    vault_client = hvac.Client(url='https://sanctuary.drud.io:8200', token=vault_token, verify=False)
    
    if vault_client.is_initialized() and vault_client.is_sealed():
        try:
            vault_client.unseal(os.getenv('VAULT_KEY_1', ''))
            vault_client.unseal(os.getenv('VAULT_KEY_2', ''))
            vault_client.unseal(os.getenv('VAULT_KEY_3', ''))
        except:
            pass
    if vault_client.is_initialized() and not vault_client.is_sealed():
        if not vault_client.is_authenticated():
            vault_client.auth_github(vault_token)
        if vault_client.is_authenticated():
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
  proxy_databag = hvac.read("secret/globals/nmdproxy")['data']
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

  vault_client.write('secret/globals/nmdproxy', **proxy_databag)

if __name__ == '__main__':
    site_proxy_entry()
