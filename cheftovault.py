#!/usr/bin/env python

import yaml
import os
import sys
from subprocess import Popen, PIPE
import hvac

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def get_vault_client():
    """
    Return a vault client if possible.
    """
    vault_addr = os.getenv("VAULT_ADDR", "https://sanctuary.drud.io:8200")
    vault_token = os.getenv('GITHUB_TOKEN', False)
    if not vault_addr or not vault_token:
        print "You must provide both VAULT_ADDR and VAULT_TOKEN environment variables."
        sys.exit(1)

    vault_client = hvac.Client(url=vault_addr)
    vault_client.auth_github(vault_token)

    if vault_client.is_initialized() and vault_client.is_sealed():
        print "Vault is initialized but sealed."
        sys.exit(1)

    if not vault_client.is_authenticated():
        print "Could not get auth."
        sys.exit(1)

    return vault_client


def get_databag(query):
    """
    Use Chef Knife to get databags

    :param query: databag path
    :return: dict of expected data
    """

    #bag_path = '/opt/.chef/nmd_encrypted_data_bag_secret'
    bag_path = "/var/jenkins_home/.chef/nmd_encrypted_data_bag_secret"
    command = 'knife data bag show {query} --secret-file {path} -F yaml'.format(
        query=query,
        path=bag_path,
    )

    #print command
    p = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    response = p.communicate()[0]

    return response


def migrate(dest="secret/databags/nmdhosting", mock=False):
    chef_sites = yaml.load(get_databag("nmdhosting"))
    vault_client = get_vault_client()
    for site in chef_sites:
        chef_path = "nmdhosting %s" % site
        vault_path = os.path.join(dest, site)
        if not mock:
            databag = yaml.load(get_databag(chef_path))
        #print yaml.dump(databag, indent=4)
        # prefix vault path with 'secret/''
        if not vault_path.startswith("secret/"):
            vault_path = os.path.join("secret", vault_path)

        print "Migrate chef databag '{0}' to vault '{1}'".format(
            chef_path,
            vault_path,
        )

        if not mock:
            if isinstance(databag, basestring):
                vault_client.write(vault_path, value=databag)
            elif isinstance(databag, dict):
                vault_client.write(vault_path, **databag)


if __name__ == '__main__':
    migrate()
