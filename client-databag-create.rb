require 'net/http'
require 'chef/rest'
require 'chef/config'
require 'chef/data_bag'
require 'chef/encrypted_data_bag_item'

sitename = ARGV[4]
type = ARGV[5]
db_server_local = ARGV[6]
db_server_staging = ARGV[7]
db_server_production = ARGV[8]
admin_username = ARGV[9]
production_domain = ARGV[10]
wp_active_theme = ARGV[11]

foo = 'moo'

# Use the same config as knife uses
Chef::Config.from_file("/var/jenkins_home/workspace/jenkins-chef-client/.chef/knife.rb")

# Get the encrypted data secret
secret = Chef::EncryptedDataBagItem.load_secret(ENV['NMDCHEF_SECRET_FILE'])

# values that are consistent across environment and platform
common = {
    :sitename => sitename,
    :type => type,
    :apache_owner => 'nginx',
    :apache_group => 'nginx',
    :aws_utf_symmetric_key => foo,
    :aws_access_key => foo,
    :aws_bucket => foo,
    :aws_secret_key => foo,
    :admin_mail => 'accounts@newmediadenver.com',
    :db_name => sitename,
    :db_username => sitename + '_db',
    :php => {
      :version => "5.5"
    },
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
      sitename + 'prod.nmdev.us',
      production_domain
    ]
}

# values that are different per platform
if type == 'wp'
    type_keys_default = {
        :auth_key => SecureRandom.base64(48).to_s,
        :secure_auth_key => SecureRandom.base64(48).to_s,
        :logged_in_key => SecureRandom.base64(48).to_s,
        :nonce_key => SecureRandom.base64(48).to_s,
        :auth_salt => SecureRandom.base64(48).to_s,
        :secure_auth_salt => SecureRandom.base64(48).to_s,
        :logged_in_salt => SecureRandom.base64(48).to_s,
        :nonce_salt => SecureRandom.base64(48).to_s,
        :docroot => '/var/www/' + sitename + '/current/htdocs',
        :url => 'localhost:1025',
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
        :docroot => '/var/www/' + sitename + '/current/htdocs',
        :url => sitename + '.nmdev.us',
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
        :docroot => '/var/www/' + sitename + '/current/htdocs',
        :url => production_domain,
        :active_theme => wp_active_theme,
    }
elsif type == 'drupal'
    type_keys_default = {
        :hash_salt => SecureRandom.base64(48).to_s,
        :cmi_active => '/var/www/' + sitename + '/current/active',
        :cmi_staging => '/var/www/' + sitename + '/current/staging',
        :docroot => '/var/www/' + sitename + '/current/docroot',
    }
    type_keys_staging = {
        :hash_salt => SecureRandom.base64(48).to_s,
        :cmi_active => '/var/www/' + sitename + '/current/active',
        :cmi_staging => '/var/www/' + sitename + '/current/staging',
        :docroot => '/var/www/' + sitename + '/current/docroot',
    }
    type_keys_production = {
        :hash_salt => SecureRandom.base64(48).to_s,
        :cmi_active => '/var/www/' + sitename + '/current/active',
        :cmi_staging => '/var/www/' + sitename + '/current/staging',
        :docroot =>'/var/www/' + sitename + '/current/docroot',
    }
end
    

# Construct a new data bag
bag_item = Chef::DataBagItem.new
bag_item.data_bag('example')
bag_item['id'] = sitename
bag_item['_default'] = [common, default, type_keys_default].reduce(:merge)
bag_item['staging'] = [common, staging, type_keys_staging].reduce(:merge)
bag_item['production'] = [common, production, type_keys_production].reduce(:merge)


# Encrypt and save new data bag
enc_hash = Chef::EncryptedDataBagItem.encrypt_data_bag_item(bag_item, secret)
ebag_item = Chef::DataBagItem.from_hash(enc_hash)
ebag_item.data_bag('example')
ebag_item.save

exit 0
