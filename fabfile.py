from __future__ import with_statement
from fabric.api import *
import time, os

env.roledefs = {
    'local': {
        'hosts': ['localhost']
    },
    'production': {
        'hosts': ['root@70.32.96.146']
    }
}

deploydir = '/var/www/vhosts/iaals.du.edu'
docroot = '/var/www/vhosts/iaals.du.edu/httpdocs'
giturl = 'git@github.com:newmediadenver/iaals.git'
gitbranch = 'master'
destination = deploydir + '/releases/' + str(int(time.time()))
archive = 'production-iaals-1438274510.tar.gz'
mysql_user = 'admin_iaalsd7'
mysql_pass = '71V&p^O&lWRaRZ12'
mysql_db = 'iaalsd7_db'

# Sub-tasks
def foo():
    #print os.environ['NMDLAMP_VERSION']
    run('mkdir /var/archives')
    put(archive, '/var/archives/%s' % archive)

def envprep():
    run('mkdir %s/releases' % deploydir)
    run('mkdir %s/shared' % deploydir)
    run('mkdir %s/shared/files' % deploydir)
    run('mkdir /var/archives')
    

def gitclone():
    run('git clone %s -b %s %s' % (giturl, gitbranch, destination))

def symlink_switch():
    run('rm %s/current && ln -s %s %s/current')

def hostname():
    run('hostname')

def deploy():
    gitclone()
    symlink_switch()


# Primary Tasks

def create():
    envprep()
    deploy()
    #put(archive, '/var/archives/%s' archive)
    with cd('/var/archives'):
        run('mkdir iaals')
        run('tar -xzf %s -C iaals' % archive)
        run('rm -rf %s/shared/files' % deploydir)
        run('mv iaals/docroot/sites/default/files %s/shared/' % deploydir)
        run('mysql -u %s -p%s %s -e \'SOURCE iaals/iaals.sql\'' % (mysql_user, mysql_pass, mysql_db))
    with cd('%s/current'):
        run('drush cc all')

def update():
    deploy()
    run('drush updb -y')
    run('drush cc all')

# def backup():
#     run('drush archive-dump')
#     run(something to download it)