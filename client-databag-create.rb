require 'net/http'
require 'chef/rest'
require 'chef/config'
require 'chef/data_bag'
require 'chef/encrypted_data_bag_item'

def to_boolean(str)
  str == 'true'
end

sitename = ARGV[4]
type = ARGV[5]
db_server_local = ARGV[6]
db_server_staging = ARGV[7]
db_server_production = ARGV[8]
admin_username = ARGV[9]
#production_domain = ARGV[10]
new_site = to_boolean(ARGV[10])
web_server_staging = ARGV[11]
web_server_prod = ARGV[12]
wp_active_theme = ARGV[13]


if web_server_prod == 'webcluster01'
    web_server_prod = [
        'web01.newmediadenver.com',
        'web02.newmediadenver.com',
        'web04.newmediadenver.com'
    ]
end

# Use the same config as knife uses
Chef::Config.from_file("#{ENV['JENKINS_HOME']}/workspace/jenkins-scripts/.chef/knife.rb")

# Get the encrypted data secret
secret = Chef::EncryptedDataBagItem.load_secret(ENV['NMDCHEF_SECRET_FILE'])

# values that are consistent across environment and platform
common = {
    :sitename => sitename,
    :type => type,
    :apache_owner => 'nginx',
    :apache_group => 'nginx',
    :admin_mail => 'accounts@newmediadenver.com',
    :db_name => sitename,
    :db_username => sitename + '_db',
    :php => {
      :version => "5.6"
    },
    :docroot => '/var/www/' + sitename + '/current/docroot'
}

# values that are different per environment
default = {
    :admin_username => admin_username,
    :admin_password => SecureRandom.hex.to_s,
    :repository => 'git@github.com:newmediadenver/' + sitename + '.git',
    :revision => 'staging',
    :db_host => db_server_local,
    :db_user_password => SecureRandom.hex.to_s,
    :server_aliases => [
      "localhost"
    ],
    :hosts => [
        "localhost"
    ]
}
staging = {
    :admin_username => admin_username,
    :admin_password => SecureRandom.hex.to_s,
    :repository => 'git@github.com:newmediadenver/' + sitename + '.git',
    :revision => 'staging',
    :db_host => db_server_staging,
    :db_user_password => SecureRandom.hex.to_s,
    :server_aliases => [
      sitename + '.nmdev.us'
    ],
    :hosts => [
        web_server_staging
    ]
}
production = {
    :admin_username => admin_username,
    :admin_password => SecureRandom.hex.to_s,
    :repository => 'git@github.com:newmediadenver/' + sitename + '.git',
    :revision => 'master',
    :db_host => db_server_production,
    :db_user_password => SecureRandom.hex.to_s,
    :server_aliases => [
      sitename + 'prod.nmdev.us'
    ],
    :hosts => [
        web_server_prod
    ]
}

# xtradb specifics
if db_server_production == 'mysql.newmediadenver.com'
    xtradb = {
        :db_port => '3307',
        :custom_port => 'enabled'
    }
else
    xtradb = {}
end

# new site
if new_site == true
    new_site = {
        :new_site => true,
        :install_profile => sitename
    }
else
    new_site = {}
end

# values that are different per platform
if type == 'wp'
    # Only need to set new_site vals in _default
    default = [default, new_site].reduce(:merge)
    type_keys_default = {
        :auth_key => SecureRandom.base64(48).to_s,
        :secure_auth_key => SecureRandom.base64(48).to_s,
        :logged_in_key => SecureRandom.base64(48).to_s,
        :nonce_key => SecureRandom.base64(48).to_s,
        :auth_salt => SecureRandom.base64(48).to_s,
        :secure_auth_salt => SecureRandom.base64(48).to_s,
        :logged_in_salt => SecureRandom.base64(48).to_s,
        :nonce_salt => SecureRandom.base64(48).to_s,
        :url => 'http://localhost:1025',
        :active_theme => wp_active_theme,
    }
    type_keys_staging = {
        :auth_key => SecureRandom.base64(48).to_s,
        :secure_auth_key => SecureRandom.base64(48).to_s,
        :logged_in_key => SecureRandom.base64(48).to_s,
        :nonce_key => SecureRandom.base64(48).to_s,
        :auth_salt => SecureRandom.base64(48).to_s,
        :secure_auth_salt => SecureRandom.base64(48).to_s,
        :logged_in_salt => SecureRandom.base64(48).to_s,
        :nonce_salt => SecureRandom.base64(48).to_s,
        :url => 'http://' + sitename + '.nmdev.us',
        :active_theme => wp_active_theme,
    }
    type_keys_production = {
        :auth_key => SecureRandom.base64(48).to_s,
        :secure_auth_key => SecureRandom.base64(48).to_s,
        :logged_in_key => SecureRandom.base64(48).to_s,
        :nonce_key => SecureRandom.base64(48).to_s,
        :auth_salt => SecureRandom.base64(48).to_s,
        :secure_auth_salt => SecureRandom.base64(48).to_s,
        :logged_in_salt => SecureRandom.base64(48).to_s,
        :nonce_salt => SecureRandom.base64(48).to_s,
        :url => 'http://' + sitename + 'prod.nmdev.us',
        :active_theme => wp_active_theme,
    }
elsif type == 'drupal'
    # Need to set new_site in all envs - add to common
    common = [common, new_site].reduce(:merge)
    type_keys_default = {
        :hash_salt => SecureRandom.base64(48).to_s,
        :cmi_sync => '/var/www/' + sitename + '/current/sync',
    }
    type_keys_staging = {
        :hash_salt => SecureRandom.base64(48).to_s,
        :cmi_sync => '/var/www/' + sitename + '/current/sync',
    }
    type_keys_production = {
        :hash_salt => SecureRandom.base64(48).to_s,
        :cmi_sync => '/var/www/' + sitename + '/current/sync',
    }
else
    type_keys_default = {}
    type_keys_staging = {}
    type_keys_production = {}
end
    

# Construct a new data bag
bag_item = Chef::DataBagItem.new
bag_item.data_bag('nmdhosting')
bag_item['id'] = sitename
bag_item['_default'] = [common, default, type_keys_default].reduce(:merge)
bag_item['staging'] = [common, staging, type_keys_staging].reduce(:merge)
bag_item['production'] = [common, production, xtradb, type_keys_production].reduce(:merge)


# Encrypt and save new data bag
enc_hash = Chef::EncryptedDataBagItem.encrypt_data_bag_item(bag_item, secret)
ebag_item = Chef::DataBagItem.from_hash(enc_hash)
ebag_item.data_bag('nmdhosting')
ebag_item.save

exit 0
