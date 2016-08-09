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
    """
    Return a vault client if possible.
    """
    # Disable warnings for the insecure calls
    requests.packages.urllib3.disable_warnings()
    vault_addr = os.getenv("VAULT_ADDR", "https://sanctuary.drud.io:8200")
    vault_token = os.getenv('GITHUB_TOKEN', False)
    if not vault_addr or not vault_token:
        print "You must provide both VAULT_ADDR and GITHUB_TOKEN environment variables."
        print "(Have you authenticated with `drud secret auth` to create your GITHUB_TOKEN?)"
        sys.exit(1)

    vault_client = hvac.Client(url=vault_addr, verify=False)
    vault_client.auth_github(vault_token)

    if vault_client.is_initialized() and vault_client.is_sealed():
        print "Vault is initialized but sealed."
        sys.exit(1)

    if not vault_client.is_authenticated():
        print "Could not get auth."
        sys.exit(1)

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
