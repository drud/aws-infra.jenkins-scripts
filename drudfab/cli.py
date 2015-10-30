#!/usr/bin/env python

import yaml
import os
import sys
import logging
import tempfile
from subprocess import Popen, PIPE
import click

import ansible.runner
import ansible.playbook
from ansible import callbacks
from ansible import utils

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
HOME_DIR = os.path.expanduser("~")
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

# get path to nmd chef repo or assume it is in the user's home
#chef_local_path = os.getenv('NMDCHEF_REPO_LOCAL', '{}/cookbooks/chef'.format(HOME_DIR))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create a file handler
handler = logging.FileHandler('fab.log')
handler.setLevel(logging.DEBUG)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)

# callbacks for ansible runner
stats = callbacks.AggregateStats()
playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)


def ansible_run(roles, hosts='localhost', variables={}, local=False, sudo=True, debug=True):
    """
    Applies ansible roles to a set of hosts by creating a temporary playbook
    and calling the ansible-playbook command.
    :param roles: The role/s to apply
    :param hosts: The host/s to apply the role/s to
    :param variables: Any additional variables to be added to the playbook
    :param local: Add 'connection: local' to playbook or not
    :param sudo: Add 'sudo: yes' to playbook or not
    :param debug: Enable debug output
    """
    #if variables['deploy_env'] == '_default':
        # add path to ansible.cfg
        #confpath = os.path.join(CURRENT_DIR, 'ansible.cfg')
        #os.system('export ANSIBLE_CONFIG=' + confpath)

    playbook = ansible_build_playbook(roles, hosts, variables, local, sudo)

    # Create a temp playbook file
    with tempfile.NamedTemporaryFile() as tmpf:
        tmpf.write(playbook)
        tmpf.flush()

        # Run the playbook
        cmd = ['ansible-playbook', '-i', 'hosts']
        if debug:
            logger.info(playbook)
            cmd += ['-vvvv']
            utils.VERBOSITY = 2
        cmd += [tmpf.name]
        print ' '.join(cmd)
        #p = Popen(' '.join(cmd), stdout=PIPE, stderr=PIPE, shell=True)
        #resp = p.communicate()[0]
        #print resp
        pb = ansible.playbook.PlayBook(
            playbook=tmpf.name,
            host_list=variables['nmdhosting']['hosts'],
            stats=stats,
            callbacks=playbook_cb,
            runner_callbacks=runner_cb,
            #check=True
        )

        results = pb.run()  # This runs the playbook
        playbook_cb.on_stats(pb.stats)

        
        failed = False
        for k, v in results.iteritems():
            if 'failures' in v and not failed:
                failed = v['failures']
        print results

        if failed:
            sys.exit(1)


def ansible_build_playbook(roles, hosts, variables=[], local=False, sudo=False, debug=False):

    playbook = {'hosts': hosts}

    if local:
        playbook.update({'connection': 'local'})
    if sudo:
        playbook.update({'sudo': 'yes'})
    if variables:
        playbook.update({'vars': variables})

    if not isinstance(roles, list):
        roles = [roles]

    # add abs path to site manage_site role (and the rest too so be careful what roles you add)
    roles = [CURRENT_DIR + '/roles/' + x for x in roles]

    playbook.update({'gather_facts': 'no'})
    playbook.update({'roles': roles})

    return yaml.dump([playbook])


def generate_vhost(data):
    nmdhosting = data['nmdhosting']
    name_clean = data['name'].replace('_', '-')
    docroot = "{0}/current/docroot".format(data['webroot'])

    directories = {
        docroot: {
            'Options': 'FollowSymLinks',
            'AllowOverride': 'All',
            'Order': 'allow,deny',
            'Allow': 'from all',
        },
        '/': {
            'Options': 'FollowSymLinks',
            'AllowOverride': 'All',
        }
    }

    # nmdhosting['php'] doesn't always exist...not sure about 'version' when 'php' exists
    php_version = '5.3'
    if 'php' in nmdhosting and 'version' in nmdhosting['php']:
        php_version = nmdhosting['php']['version']

    if php_version == '5.5':
      php_sock = 'php55-fpm.sock'
    else:
      php_sock = 'php53-fpm.sock'

    fastcgi_buffer_size = nmdhosting['fastcgi']['fastcgi_buffer_size'] if 'fastcgi' in nmdhosting else '8k'
    fastcgi_buffers = nmdhosting['fastcgi']['fastcgi_buffers'] if 'fastcgi' in nmdhosting else '64 4k'
    fastcgi_busy_buffers_size = nmdhosting['fastcgi']['fastcgi_busy_buffers_size'] if 'fastcgi' in nmdhosting else '224k'

    if data['deploy_env'] in ['nmdhosting', 'ldap']:
        ldap = data['ldap']
        directories = {
            docroot: {
                'Options': 'FollowSymLinks',
                'AllowOverride': 'All',
                'Order': 'allow,deny',
                'Allow': 'from all',
            },
            '/': {
                'Options': 'FollowSymLinks',
                'AuthName': '"NEWMEDIA!"',
                'AuthType': 'Basic',
                'AllowOverride': 'All',
                'AuthBasicProvider': 'ldap',
                'AuthLDAPBindDN': ldap['bind_dn'],
                'AuthLDAPBindPassword': ldap['bind_password'],
                'AuthLDAPGroupAttribute': ldap['group_attribute'],
                'AuthLDAPGroupAttributeIsDN': ldap['group_attribute_is_dn'],
                'AuthLDAPURL': ldap['url'],
                'Require': ldap['require']
            }
        }

    vhost = {
        'port': 80,
        'server_name': name_clean,
        'server_aliases': data['nmdhosting']['server_aliases'],
        'docroot': docroot,
        'directories': directories,
        'log_level': 'info',
        'error_log': "/var/log/httpd/{0}-error.log".format(data['name']),
        'custom_log':  "/var/log/httpd/{0}-access.log combined".format(data['name']),
        'rewrite_engine': 'on',
        'rewrite_log': "/var/log/httpd/{0}-rewrite.log".format(data['name']),
        'rewrite_log_level': 0,
        'redirect_matches': {
            '[A-Z].*\.txt': '/'
        },
        'rewrite': [
            {
                'conditions': [
                    "%{HTTP_HOST} !^" + name_clean + ".localhost.dev [NC]",
                    '%{HTTP_HOST} !^$',
                ],
                'rules': [
                    "^/(.*)$ http://{0}.localhost.dev/$1 [L,R=301]".format(name_clean),
                ],
            },
        ],
        'php_sock': php_sock,
        'fastcgi_buffer_size': fastcgi_buffer_size,
        'fastcgi_buffers': fastcgi_buffers,
        'fastcgi_busy_buffers_size': fastcgi_busy_buffers_size
    }

    if data['action'] == 'create':
        # Modify the basic_web_app to suite.
        vhost['rewrite'] = []

    return vhost


def get_env_data(name, action, deploy_env):
    """
    Use Chef Knife to get json about hosting and databases

    :param client: name of client
    :return: dict of expected data
    """
    current_dir = os.getcwd()
    #os.chdir(chef_local_path)
    outputs = {
        'name': str(name),
        'action': action,
        'deploy_env': deploy_env,
    }


    inputs = {
        'nmdhosting': ('nmdhosting', name),
        'nmddb': ('nmddb', 'mysql'),
        'nmddrupal': ('nmddrupal', 'aws'),
        'phpfpm': ('nmdhosting', 'phpfpm'),
    }

    if deploy_env in ['staging', '_default']:
        inputs['ldap'] = ('nmdhosting', 'ldap')

    commands = []
    for key, ins in inputs.iteritems():

        bag_path = '/var/jenkins_home/.chef/nmd_encrypted_data_bag_secret'
        command = 'knife data bag show {input} --secret-file {path} -F yaml -c $JENKINS_HOME/workspace/jenkins-scripts/.chef/knife.rb'.format(
            input=' '.join(ins),
            path=bag_path,
        )

        print command
        p = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
        commands.append((key, p))

    for proc in commands:
        key = proc[0]
        process = proc[1]
        response = process.communicate()[0]

        response = clean_data(response)

        data = yaml.load(response)
        outputs[key] = data[deploy_env]
        # this is for url replacing for wordpress?
        if key == 'nmdhosting':
            outputs['all_hosting'] = data

    nmdhosting = outputs['nmdhosting']
    nmddrupal = outputs['nmddrupal']

    # determine site type
    if 'type' in nmdhosting:
        outputs['site_type'] = nmdhosting['type']
        # change 'wp' to 'wordpress'
        if outputs['site_type'] == 'wp':
            outputs['site_type'] = 'wordpress'
    else:
        if 'auth_key' in nmdhosting:
            outputs['site_type'] = 'wordpress'
        else:
            outputs['site_type'] = 'drupal'

    # determine whether site is imported or installed
    outputs['new_site'] = nmdhosting['new_site'] if 'new_site' in nmdhosting else False
    outputs['install_profile'] = nmdhosting['install_profile'] if 'install_profile' in nmdhosting else 'standard'

    outputs['webroot'] = '/var/www/{0}'.format(name)
    outputs['docroot'] = nmdhosting['docroot'] if 'docroot' in nmdhosting else outputs['webroot'] + '/current'
    # Directory to download archives into
    outputs['archivedir'] = '/var/archives'

    # wordpress specific
    if outputs['site_type'] == 'wordpress':
        outputs['wp_generic'] = nmdhosting['wp_generic'] if 'wp_generic' in nmdhosting else False
        outputs['wp_prefix'] = nmdhosting['prefix'] if 'prefix' in nmdhosting else 'wp_'

        # set the archive for the create process
        nmdhosting_dev = outputs['all_hosting']['_default']
        nmdhosting_staging = outputs['all_hosting']['staging']
        nmdhosting_production = outputs['all_hosting']['production']
        if outputs['deploy_env'] in ['_default']:
            search_replace = "wp -p5.5 search-replace '{0}' '{1}' --all-tables --quiet --allow-root".format(nmdhosting_staging['url'], nmdhosting['url'])
            search_replace += " && wp -p5.5 search-replace '{0}' '{1}' --all-tables --quiet --allow-root".format(nmdhosting_production['url'], nmdhosting['url'])
        elif outputs['deploy_env'] in ['staging']:
            search_replace = "wp -p5.5 search-replace '{0}' '{1}' --all-tables --quiet --allow-root".format(nmdhosting_dev['url'], nmdhosting['url'])
            search_replace += " && wp -p5.5 search-replace '{0}' '{1}' --all-tables --quiet --allow-root".format(nmdhosting_production['url'], nmdhosting['url'])
        else:
            search_replace = "wp -p5.5 search-replace '{0}' '{1}' --all-tables --quiet --allow-root".format(nmdhosting_dev['url'], nmdhosting['url'])
            search_replace += " && wp -p5.5 search-replace '{0}' '{1}' --all-tables --quiet --allow-root".format(nmdhosting_staging['url'], nmdhosting['url'])

        outputs['search_replace'] = search_replace
        
    # drupal specific
    else:
        if outputs['action'] == 'create':
            si_cmd = "drush si -y {2} --clean-url=1 --site-name='{1}' ".format(outputs['webroot'], outputs['name'], outputs['install_profile'])
            si_cmd += "--account-name='{0}' ".format(nmdhosting['admin_username'])
            si_cmd += "--account-pass='{0}' ".format(nmdhosting['admin_password'])
            si_cmd += "install_configure_form.update_status_module='array(FALSE,FALSE)' "
            si_cmd += "install_configure_form.date_default_timezone='America/Denver'"
            outputs['si_cmd'] = si_cmd

    if outputs['action'] in ['update', 'delete', 'backup']:
        update_cmd = "export AWS_ACCESS_KEY='{0}' ".format(nmddrupal['aws_access_key'])
        update_cmd += "&& export AWS_SECRET_KEY='{0}' ".format(nmddrupal['aws_secret_key'])
        update_cmd += "&& export AWS_UTF_SYMMETRIC_KEY='{0}' ".format(nmddrupal['aws_utf_symmetric_key'])
        update_cmd += "&& sh {0}/shared/s3archive.sh".format(outputs['webroot'])
        outputs['archive_cmd'] = update_cmd

    # permissions.sh directories
    if 'perms_directories' not in nmdhosting:
        # wordpress
        if 'auth_key' in nmdhosting:
            outputs['nmdhosting']['perms_directories'] = [
                "{0}/shared/uploads".format(outputs['webroot']),
                "{0}/current".format(outputs['webroot'])
            ]
        # drupal
        else:
            outputs['nmdhosting']['perms_directories'] = [
                '{0}/shared/files'.format(outputs['webroot']),
                '{0}/current'.format(outputs['webroot']),
                '{0}/current/docroot/sites/all'.format(outputs['webroot']),
                '{0}/current/docroot/sites/default'.format(outputs['webroot']),
            ]

    # generate vhost config
    outputs['vhost'] = generate_vhost(outputs)
    # set server type to nginx if no owner specified
    outputs['server_type'] = nmdhosting['apache_owner'] if 'apache_owner' in nmdhosting else 'nginx'
    # assumer d7 settings template if not explicitly set
    outputs['settings_source'] = nmdhosting['settings_source'] if 'settings_source' in nmdhosting else 'd7.settings.php.j2'
    if 'files_directory' in nmdhosting:
       outputs['files_directory'] = nmdhosting['files_directory']
    if 'nginx_client_max_body' in nmdhosting:
        outputs['max_upload_size'] = nmdhosting['nginx_client_max_body']
    elif 'nginx_client_max_body' in outputs['phpfpm']:
        outputs['max_upload_size'] = outputs['phpfpm']['nginx_client_max_body']

    #os.chdir(current_dir)
    return outputs


def clean_data(data):
    """
    Find potential issues in the databags

    :param data:
    :return:
    """
    needles = [
        '{{',
        '}}',
    ]
    # find the problem string and print its location
    for needle in needles:
        for i, line in enumerate(data.split('\n')):
            loc = line.find(needle)
            if loc > -1:
                print 'found an issue in the data: {0}'.format(needle)
                print 'context: line: {0} '.format(i), line[max(0, loc - 15):loc + 15]
        data = data.replace(needle, '')

    return data


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='1.0.0')
def siteman():
    pass


@siteman.command()
@click.option('--client')
@click.option('--debug', is_flag=True)
@click.option('--local', is_flag=True)
@click.option('--env', default='_default')
def create(client, debug, local, env):
    vars = get_env_data(client, action='create', deploy_env=str(env))
    ansible_run(['manage_site'], hosts='all', variables=vars, local=local, sudo=True, debug=debug)


@siteman.command()
@click.option('--client')
@click.option('--debug', is_flag=True)
@click.option('--local', is_flag=True)
@click.option('--env', default='_default')
def update(client, debug, local, env):
    vars = get_env_data(client, action='update', deploy_env=str(env))
    ansible_run(['manage_site'], hosts='all', variables=vars, local=local, sudo=True, debug=debug)


@siteman.command()
@click.option('--client')
@click.option('--debug', is_flag=True)
@click.option('--local', is_flag=True)
@click.option('--env', default='_default')
def backup(client, debug, local, env):
    vars = get_env_data(client, action='backup', deploy_env=str(env))
    ansible_run(['manage_site'], hosts='all', variables=vars, local=local, sudo=True, debug=debug)


@siteman.command()
@click.option('--client')
@click.option('--debug', is_flag=True)
@click.option('--local', is_flag=True)
@click.option('--env', default='_default')
def delete(client, debug, local, env):
    vars = get_env_data(client, action='delete', deploy_env=str(env))
    ansible_run(['manage_site'], hosts='all', variables=vars, local=local, sudo=True, debug=debug)


if __name__ == '__main__':
    siteman()
