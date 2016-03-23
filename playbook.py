#!/usr/bin/env python
import os
import click
import json
import logging

def format_command(command, c, bundler):
    if not bundler:
        command += ' --no-bundler'
    if c:
        command += ' --c {0}'.format(c)
    return command

def get_databags():
    # return {
    #     "drud/base": "/ansibleroles/ansible.base/vars",
    #     "drud/ntp": "/ansibleroles/ansible.ntp/vars",
    #     "drud/logwatch": "/ansibleroles/ansible.logwatch/vars",
    #     "drud/postfix": "/ansibleroles/ansible.postfix/vars",
    #     "drud/fail2ban": "/ansibleroles/ansible.fail2ban/vars",
    #     "drud/jumpcloud": "/ansibleroles/ansible.jumpcloud/vars",
    #     "drud/nginx": "/ansibleroles/ansible.nginx/vars",
    #     "drud/certs": "/ansibleroles/ansible.certs/vars",
    #     "drud/haproxy_xtradb": "/ansibleroles/ansible.haproxy_xtradb/vars",
    #     "drud/phpfpm": "/ansibleroles/ansible.phpfpm/vars",
    #     "drud/composer": "/ansibleroles/ansible.composer/vars",
    #     "drud/drush": "/ansibleroles/ansible.drush/vars",
    #     "drud/wpcli": "/ansibleroles/ansible.wpcli/vars",
    #     "drud/nodejs": "/ansibleroles/ansible.nodejs/vars",
    #     "drud/gluster_client": "/ansibleroles/ansible.gluster_client/vars",
    #     "drud/percona": "/ansibleroles/ansible.percona/vars",
    #     "drud/nagios-client": "/ansibleroles/ansible.nagios_client/vars",
    #     "drud/s3": "/ansibleroles/ansible.s3/vars",
    # }
    return {}


def generate_variables(databag, env, c, bundler):
    cd = os.getcwd()
    os.system(cd + "/generatevars.py " + databag + " " + cd + "/ --f json")
    with open(cd + '/generated.json') as data_file:
        data = json.load(data_file)
        # data['ssh_username'] = data['vpc']['ssh_username']
        # data['region'] = data['vpc']['region']
        # data['base_ami'] = data['vpc']['amis']['base']
        # if 'vpc_id' in data['vpc']['state']['modules'][0]['outputs']:
        #     data['vpc_id'] = data['vpc']['state']['modules'][0]['outputs']['vpc_id']
        #     data['subnet_id'] = data['vpc']['state']['modules'][0]['outputs']['subnet.public']

        # delete_keys = ['vpc', 'kube_clusters', 'kube_secrets', 'clients', 'apps']

        # for key in delete_keys:
        #     if key in data:
        #         del data[key]

    with open(cd + '/generated.json', 'w') as outfile:
        json.dump(data, outfile)

    databags = get_databags()
    for databag in databags:
        os.system(format_command('{0}/generatevars.py {1} {0}/{2} --e={3}'.format(cd, databag, databags[databag], env), c, bundler))

def remove_variables():
    cd = os.getcwd()

    os.system("rm -f " + cd + "/generated.json")

    databags = get_databags()
    for databag in databags:
        os.system("rm -f " + cd + databags[databag] + "/generated.json")

def ansible_it(target_host, aws_environment, ansible_tags, aws_ssh_user, extra_vars=""):
    drud_jumpcloud_client_id = os.getenv('DRUD_JUMPCLOUD_CLIENT_ID')
    jenkins_home = os.getenv('JENKINS_HOME')
    cmd = 'ansible-playbook'
    cmd += ' -e "drud_jumpcloud_client_id={drud_jumpcloud_client_id} {extra_vars}"'.format(drud_jumpcloud_client_id=drud_jumpcloud_client_id, extra_vars=extra_vars)
    cmd += ' -i /etc/ansible/hosts'
    cmd += ' -vv'
    cmd += ' --private-key /var/jenkins_home/.ssh/aws.pem'
    cmd += ' -u {aws_ssh_user}'.format(aws_ssh_user=aws_ssh_user)
    cmd += ' --tags {ansible_tags}'.format(ansible_tags=ansible_tags)
    cmd += ' {jenkins_home}/workspace/jenkins-ansible/hosts/{target_host}.yml'.format(jenkins_home=jenkins_home,target_host=target_host)
    os.system(cmd)


@click.command()
@click.option('--loglevel',
    default='INFO',
    help='log level: DEBUG, INFO, WARNING, ERROR, CRITICAL'
)
@click.option('--databag',
    help='The databag to work with eg: drud/aws'
)
@click.option('--env',
    help='The env to work with: _default, staging, production',
    default='_default'
)
@click.option(
    '--c',
    help='The location of an optional knife.rb configuration file to use.'
)
@click.option(
    '--bundler/--no-bundler',
    default=True
)
@click.option('--target-host')
@click.option('--aws-environment')
@click.option('--ansible-tags')
@click.option('--aws-ssh-user')
def request_router(loglevel, databag, env, c, bundler, target_host, aws_environment, ansible_tags, aws_ssh_user):
    numeric_level = getattr(logging, loglevel.upper(), None)
    logging.basicConfig(level=numeric_level, format='[%(levelname)s %(module)s:%(lineno)s %(funcName)s] %(message)s')
    generate_variables(databag, env, c, bundler)
    ansible_it(target_host, aws_environment, ansible_tags, aws_ssh_user)
    remove_variables()

if __name__ == '__main__':
    request_router()
