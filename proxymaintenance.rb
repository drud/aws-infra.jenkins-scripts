require 'net/http'
require 'chef/rest'
require 'chef/config'
require 'chef/data_bag'
require 'chef/encrypted_data_bag_item'

bagname = 'nmdproxy'
appname = 'upstream'

environment = ARGV[4]
server = /^([^.]*)/.match(ARGV[5]).to_s
sitename = ARGV[6]
action = ARGV[7]

puts environment
puts server
puts sitename
puts action

# Use the same config as knife uses
Chef::Config.from_file("#{ENV['JENKINS_HOME']}/workspace/jenkins-scripts/.chef/knife.rb")

# Get the encrypted data secret
secret = Chef::EncryptedDataBagItem.load_secret(ENV['NMDCHEF_SECRET_FILE'])

# Load the client data bag
client = Chef::EncryptedDataBagItem.load('nmdhosting', sitename, secret)
# Get the server_aliases values we need to move in proxy
aliases = client[environment]['server_aliases']

# Load the proxy data bag
item = Chef::EncryptedDataBagItem.load(bagname, appname, secret)
# Get the environment data we are altering
update = item[environment]

if action == 'add'
    aliases.each do |key|
        puts update[server]['apps'][key]
        if update[server]['apps'][key].nil?
            update[server]['apps'][key] = {"maintenance" => true}
        else
            update[server]['apps'][key]['maintenance'] = true
        end
        puts update[server]['apps'][key]
    end
elsif action == 'remove'
    aliases.each do |key|
        puts update[server]['apps'][key]
        update[server]['apps'][key].delete("maintenance")
        puts update[server]['apps'][key]
    end
else
    abort "Invalid action #{action}"
end

# Construct a new data bag
bag_item = Chef::DataBagItem.new
bag_item.data_bag(bagname)
bag_item['id'] = appname
bag_item['_default'] = item['_default']
# Determine which environment we are altering in update
bag_item['staging'] = item['staging']
bag_item['staging'] = update unless environment != 'staging'
bag_item['production'] = item['production']
bag_item['production'] = update unless environment != 'production'

# Encrypt and save new data bag
enc_hash = Chef::EncryptedDataBagItem.encrypt_data_bag_item(bag_item, secret)
ebag_item = Chef::DataBagItem.from_hash(enc_hash)
ebag_item.data_bag(bagname)
ebag_item.save

exit 0
