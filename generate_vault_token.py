import requests
import hvac
import os, sys

file_name = "vault_token.txt"

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

    with open(file_name, 'w') as fp:
        fp.write(vault_client.token)
        file_path = "{path}/{file}".format(path=os.getcwd(), file=file_name)

    print "Successfully generated a vault token and wrote it to: {path}".format(path=file_path)

    

if __name__ == '__main__':
    get_vault_client()