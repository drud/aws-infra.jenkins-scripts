#!/usr/bin/python
import databag
import click
import sys

debug=False

proxy_container="nmdproxy"
if debug:
  proxy_container="nmdtest"

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
  proxy_databag = databag.get_databag(bag_name="upstream", container=proxy_container)
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
      site_entries[url]["auth"] = "true"
    if www_force:
      site_entries[url]["www_force"] = "true"
    if ssl:
      site_entries[url]["ssl"] = ssl
    if ssl_force:
      site_entries[url]["ssl_force"] = "true"
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

  databag.save_databag(proxy_databag, bag_name="upstream", container=proxy_container)

# if __name__ == '__main__':
#   site_proxy_entry("mytest.nmdev.us", "staging", operation="add")
#   site_proxy_entry("mytestprod.nmdev.us", "production", operation="add")
if __name__ == '__main__':
    site_proxy_entry()
