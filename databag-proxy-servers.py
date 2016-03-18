#!/usr/bin/python
import databag
import click

debug=True

proxy_container="nmdproxy"
if debug:
  proxy_container="nmdtest"
#### Logic for taking servers in and out of rotation ####
#Here's the servers array:
# bag['production']['webcluster01']['servers'] = [
#   "server web01.newmediadenver.com:80;",
#   "server web02.newmediadenver.com:80;",
#   "server web04.newmediadenver.com:80;"
# ]
def remove_server(servers, server_to_remove):
  """
  Removes a server from the list.

  :param servers: The url entry to add to the databag
  :param server_to_remove: The name of just the server or the full server string

  :returns list of servers
  """
  index_to_remove = None
  for index, server in enumerate(servers):
    if server_to_remove in server:
      index_to_remove = index
      break
  if index_to_remove:
    servers.pop(index_to_remove)
  else:
    print "Could not find a server {server} in [{servers}] to remove.".format(server=server_to_remove,servers=",".join(servers))
  return servers

def add_server(servers, server_to_add):
  """
  Add a server to the list.

  :param servers: The url entry to add to the databag
  :param server_to_add: The name of just the server or the full server string

  :returns list of servers
  """
  # Fix the format if necessary
  if "server " not in server_to_add:
    server_to_add="server {server}".format(server=server_to_add)
  if ":80;" not in server_to_add:
    server_to_add="{server}:80;".format(server=server_to_add)

  if any([server_to_add==server for server in servers]):
    print "Server '{server}' already exists in rotation. No action is required".format(server=server_to_add)
    return True
  else:
    print "Adding server '{server}' to webcluster01."
    servers=servers.append(server_to_add)
  return servers

def get_server_list(environment):
  """
  Get the list of servers for an environment

  :param environment: 'staging' or 'production'

  :returns list of servers
  """
  proxy_databag = databag.get_databag("upstream", container=proxy_container)
  if environment=='production':
    server_list = proxy_databag[environment]['webcluster01']['servers']
  elif environment=="staging":
    server_list = proxy_databag[environment]['web01']['servers']
  else:
    raise Exception("Unrecognized environment of '{environment}. Available options are 'production' and 'development'".format(environment=environment))
    return None
  return server_list

@click.command()
@click.option('--server', prompt="Server name:", help="Name of the server you would like to add/remove")
@click.option('--environment', prompt="Which environment?", help="'staging' or 'production'", type=click.Choice(['staging', 'production']))
@click.option('--add', 'operation', flag_value='add', default=True)
@click.option('--remove', 'operation', flag_value='remove')
def modify_server_list(server, environment, operation):
  """
  Get the list of servers for an environment
  """
  proxy_databag = databag.get_databag("upstream", container=proxy_container)
  if environment=="production":
    server_list = proxy_databag[environment]['webcluster01']['servers']
  elif environment=="staging":
    server_list = proxy_databag[environment]['web01']['servers']
  else:
    raise Exception("Unrecognized environment of '{environment}. Available options are 'production' and 'development'".format(environment=environment))
    return None
  if operation == "add":
    server_list = add_server(server_list, server)
  elif operation == "remove":
    server_list = remove_server(server_list, server)
  else:
    print "Unrecognized server operation of '{operation}'".format(operation=operation)
  # Put it all back together
  if environment=="production":
    proxy_databag[environment]['webcluster01']['servers'] = server_list
  elif environment=="staging":
    proxy_databag[environment]['web01']['servers'] = server_list

  databag.save_databag(proxy_databag, bag_name="upstream", container=proxy_container)
  return True

# if __name__ == '__main__':
#   modify_server_list(server="fakeweb07.newmediadenver.com", environment="production", operation="add")
#   modify_server_list(server="fakeweb06.nmdev.us", environment="staging", operation="add")
if __name__ == '__main__':
  modify_server_list()
