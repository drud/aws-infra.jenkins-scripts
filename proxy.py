#!/usr/bin/python
# Interface for interacting with the proxy layer
import os,sys
import subprocess
import json
from pprint import pprint as p
import ast
import click
import ast
import requests
import hvac
import copy


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
    vault_addr = os.getenv("VAULT_ADDR", "https://vault.drud.com:8200")
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

def recompute_proxy_data(nmdproxy_orig, deploy_env, hostname, action):
    """
    The proxy layer is arranged so that when you are trying to
    find the information for a specific application, it is not
    predictably in the same place. nmdproxy[environment] works, 
    but X in nmdproxy[environment][X][apps] is not a predictable
    variable. This function takes the proxy data and reorganizes
    it into something more digestible by ansible Jinja2 templates
    """
    nmdproxy = copy.copy(nmdproxy_orig)
    proxy = {}
    for env_name, env in nmdproxy.items():
        # All databags/* secrets have an id field - bypass
        if env_name == "id":
            continue
        for pool_name, top_level_app in env.items():
            if 'apps' in top_level_app:
                apps = top_level_app['apps']
            # Accounts for redirect different structure
            elif 'apps' == pool_name and env_name == "_redirect":
                apps = env['apps']
            else:
                print "Warning: Could not process the following section of the 'databags/nmdproxy/upstream' secret: \n\tenv: {env} \n\tpool: {pool} \n\tapp: {app}".format(env=env_name, pool=pool_name, app=str(top_level_app))

            for app_name, app in apps.items():
                # If we're doing a redirect then we want to bypass other entries in the proxy layer
                if action == 'redirect' and env_name != '_redirect':
                    continue
                # Capture the specific host entry - we don't need to populate the rest of the proxy layer if this is running a single client site (as opposed to a full rebuild)
                # Or if the running action is a rebuild or place playbook, then we need to build out the entire proxy layer
                if hostname == app_name or (action in ['rebuild', 'place_playbook', 'redirect'] and env_name in [deploy_env, '_redirect']):
                    proxy[app_name] = app
                    proxy[app_name]['pool_name'] = pool_name
                    proxy[app_name]['env_name'] = env_name
                    proxy[app_name]['servers'] = '_redirect' if env_name == "_redirect" else top_level_app['servers']
                    proxy[app_name]['dest'] = '' if 'dest' not in app else app['dest']
                    setup_proxy_cert_paths(proxy, app_name)

    return proxy

def get_proxy():
  vault = get_vault_client()
  proxy = vault.read('secret/databags/nmdproxy/upstream')['data']
  return proxy