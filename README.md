jenkins-scripts
===============

Scripts that are used in Jenkins jobs.

---

Usage: databag-proxy-entries.py [OPTIONS]

  Add or remove entries from a proxy-structured datBabag.

Options:
  --url TEXT                      URL of server you're trying to add
  --environment [staging|production]
                                  'staging' or 'production'
  --add                           Add this entry to the proxy bag
  --remove                        Remove this entry from the proxy bag
  --auth                          Adds an auth screen
  --www-force                     Forces the url to rewrite to www.*
  --ssl-force                     Force a rewrite to https
  --ssl TEXT                      String that lines up with the SSL entry in
                                  the auth databag
  --help                          Show this message and exit.
        
At minimum, you need to have these flags defined:
./databag-proxy-servers.py --server --environment --add
./databag-proxy-servers.py --server --environment --remove

---
Usage: databag-proxy-servers.py [OPTIONS]

  Get the list of servers for an environment

Options:
  --server TEXT                   Name of the server you would like to
                                  add/remove
  --environment [staging|production]
                                  'staging' or 'production'
  --add
  --remove
  --help                          Show this message and exit.
./databag-proxy-entries.py --url --environment --add
./databag-proxy-entries.py --url --environment --remove

