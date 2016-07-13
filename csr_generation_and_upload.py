# A job for creating and managing key generation

from os import environ, remove, path
import subprocess

jenkins_scripts = environ.get("JENKINS_SCRIPTS")
aws_access_key = environ.get("AWS_ACCESS_KEY")
aws_secret_key = environ.get("AWS_SECRET_KEY")

domain_name=environ.get('Domain_Name')
state=environ.get('State')
city=environ.get('City')
legal_name=environ.get('Legal_Name')
bucket=environ.get('Databag_Name')

if path.exists("/tmp/{domain_name}.csr".format(domain_name=domain_name)):
	remove("/tmp/{domain_name}.csr".format(domain_name=domain_name))

if path.exists("/tmp/{domain_name}.key".format(domain_name=domain_name)):
	remove("/tmp/{domain_name}.key".format(domain_name=domain_name))

# Enter the required information about the company
# Run the SSL command
command='openssl req -new -newkey rsa:2048 -nodes -out /tmp/{domain_name}.csr -keyout /tmp/{domain_name}.key -subj'.format(domain_name=domain_name).split(" ")
command+=['/C=US/ST={state}/L={city}/O={legal_name}/CN={domain_name}'.format(state=state, city=city, legal_name=legal_name, domain_name=domain_name)]
out = subprocess.check_output(command, stderr=subprocess.STDOUT)

# Upload the CSR file to EC2
command="s3upload -l DEBUG -k {aws_access_key} -sk {aws_secret_key} -f -np 8 -s 100 /tmp/{domain_name}.csr s3://nmdarchive/{bucket}/{domain_name}.csr".format(aws_access_key=aws_access_key,aws_secret_key=aws_secret_key,domain_name=domain_name, bucket=bucket)
out = subprocess.check_output(command.split(" "), stderr=subprocess.STDOUT)

# Upload the KEY file to EC2
command="s3upload -l DEBUG -k {aws_access_key} -sk {aws_secret_key} -f -np 8 -s 100 /tmp/{domain_name}.key s3://nmdarchive/{bucket}/{domain_name}.key".format(aws_access_key=aws_access_key,aws_secret_key=aws_secret_key,domain_name=domain_name, bucket=bucket)
out = subprocess.check_output(command.split(" "), stderr=subprocess.STDOUT)


# Clean-up the local files
remove("/tmp/{domain_name}.csr".format(domain_name=domain_name))
remove("/tmp/{domain_name}.key".format(domain_name=domain_name))

# Input them into the nmdproxy/certs databag? TODO

# Show the nmd file commands to pull the files and share them
print "Your cert files have been uploaded to the nmdarchive. To download them, copy paste the following text into iTerm:\n"
print "mkdir ~/Downloads/{bucket} &&".format(bucket=bucket)
print "cd ~/Downloads/{bucket} &&".format(bucket=bucket)
print "nmd file get {bucket}/{domain_name}.key &&".format(bucket=bucket, domain_name=domain_name)
print "nmd file get {bucket}/{domain_name}.csr &&".format(bucket=bucket, domain_name=domain_name)
print "open ."