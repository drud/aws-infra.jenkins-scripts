import databag
import click

def site_proxy_entry(url, environment, operation="add", auth=False, www_force=False, ssl=None, ssl_force=False):
  """
  Add or remove entries from a proxy-structured databag.

  :param url: The url entry to add to the databag
  :param environment: '_default', 'staging' or 'production'
  :param operation: 'add' or 'remove' the entry
  :param auth: If set to true, will add the auth screen
  :param www_force: If set to true, will force the url to rewrite to www.*
  :param ssl: String that lines up with the SSL entry in the auth databag
  :param ssl_force: Force a rewrite to https

  :returns dict databag
  """
  proxy_databag = databag.get_databag(bag_name="upstream", container="nmdtest")
  if environment=='production':
    site_entries = proxy_databag[environment]['webcluster01']['apps']
  elif environment=="staging":
    site_entries = proxy_databag[environment]['web01']['apps']
  else:
    raise Exception("Unrecognized environment of '{environment}. Available options are 'production' and 'development'".format(environment=environment))
    return None

  if operation == "add":
    site_entries[url] = {}
    if auth==True:
      site_entries[url]["auth"] = "true"
    if www_force==True:
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

  databag.save_databag(proxy_databag, bag_name="upstream", container="nmdtest")

if __name__ == '__main__':
  site_proxy_entry("mytest.nmdev.us", "staging", operation="add")
  site_proxy_entry("mytestprod.nmdev.us", "production", operation="add")