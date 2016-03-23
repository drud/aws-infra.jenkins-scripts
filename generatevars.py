#!/usr/bin/env python
import click
import os
from subprocess import Popen, PIPE
import yaml
import json

@click.command()
@click.option('--e', default='_default', help='The desired environment: _default, staging or production')
@click.option('--f', default='yaml', help='The desired output format: yaml or json')
@click.option('--c', help='The location of an optional knife.rb configuration file to use.')
@click.option('--bundler/--no-bundler', default=True)
@click.argument('databag')
@click.argument('path')
def process_databag(e, f, c, bundler, databag, path):
    """
    Reads a NMD databag from a configured machine and writes the data in either
    generated.json or generated.yaml into a given directory.
    :param f: The desired output format: yaml or json
    :param e: The desired environment: _default, staging or production
    :param databag: The databag to translate. eg: nmdhosting/1fee
    :param path: The path to write either generated.json or generated.yaml
    """
    current_dir = os.getcwd()
    if not os.getenv('NMDCHEF_REPO_LOCAL'):
        raise Exception('NMDCHEF_REPO_LOCAL is not a vaild environment variable')
    if not os.getenv('NMDCHEF_SECRET_FILE'):
        raise Exception('NMDCHEF_SECRET_FILE is not a vaild environment variable')

    os.chdir(os.getenv('NMDCHEF_REPO_LOCAL'))
    secret = os.getenv('NMDCHEF_SECRET_FILE')
    db = databag.split('/')[0]
    db_item = databag.split('/')[1]
    knife_cmd = 'knife'
    if bundler:
        knife_cmd = 'bundle exec knife'
    command = '{4} data bag show {2} {3} --secret-file {0} -F {1}'.format(
        secret, f, db, db_item, knife_cmd)
    if c:
        command += ' -c {0}'.format(c)
    print command
    p = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = p.communicate()
    if p.returncode != 0:
        raise Exception(err)

    if f == 'json':
        data = json.loads(out)
        destination = '{0}/generated.json'.format(os.path.abspath(path))
        output = json.dumps(data[e])
    else:
        data = yaml.load(out)
        destination = '{0}/generated.yml'.format(os.path.abspath(path))
        output = yaml.dump(data[e], canonical=True)
    os.chdir(current_dir)
    with open(destination, 'w') as outfile:
        outfile.write(output)

if __name__ == '__main__':
    process_databag()
