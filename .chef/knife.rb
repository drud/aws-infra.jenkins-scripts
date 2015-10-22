# See http://docs.opscode.com/config_rb_knife.html
# for more information on knife configuration options

current_dir = File.dirname(__FILE__)
log_level :info
log_location STDOUT
node_name "jenkins_ac"
client_key "/var/jenkins_home/.chef/chef_clientkey.pem"
validation_client_name "newmediadenver-validator"
validation_key "/var/jenkins_home/.chef/chef_validationkey.pem"
chef_server_url "https://api.opscode.com/organizations/newmediadenver"
cache_type 'BasicFile'
cache_options('path' =>  "#{ENV['HOME']}/.chef/checksums")
syntax_check_cache_path  "#{ENV['HOME']}/.chef/syntax_check_cache"
secret_file "/var/jenkins_home/.chef/nmd_encrypted_data_bag_secret"
