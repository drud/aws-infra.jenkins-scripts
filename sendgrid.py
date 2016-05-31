#!/usr/bin/python
import requests
import click
import json
import os
# Sendgrid API
# Contacts API
# https://sendgrid.com/docs/API_Reference/Web_API_v3/Marketing_Campaigns/contactdb.html#Add-a-Single-Recipient-to-a-List-POST

# Add a group of recipients
# POST https://api.sendgrid.com/v3/contactdb/recipients
# Response:
# {
#   "error_count": 1,
#   "error_indices": [
#     2
#   ],
#   "new_count": 2,
#   "persisted_recipients": [
#     "YUBh", <= ID of user 1
#     "bWlsbGVyQG1pbGxlci50ZXN0"
#   ],
#   "updated_count": 0,
#   "errors": [
#     {
#       "message": "Invalid email.",
#       "error_indices": [
#         2
#       ]
#     }
#   ]
# }
# curl --request POST \
#   --url https://api.sendgrid.com/v3/mail/send/beta \
#   --header 'Authorization: Bearer YOUR_API_KEY' \
#   --header 'Content-Type: application/json' \
#   --data '{"personalizations": [{"to": [{"email": "YOU@sendgrid.com"}]}],"from": {"email": "dx@sendgrid.com"},"subject": "Hello, World!","content": [{"type": "text/plain", "value": "Heya!"}]}'
header = {
  "Authorization": "Bearer {api_key}".format(api_key=os.environ.get("SENDGRID_API_KEY")),
  "Content-Type": "application/json"
}
def add_recipient(first_name, last_name, email, customer_business_name, customer_staging_site, customer_production_site):
  add_recipient_url = 'https://api.sendgrid.com/v3/contactdb/recipients'
  contacts = [
    {
      "email": email,
      "last_name": last_name,
      "first_name": first_name,
      "customer_business_name": customer_business_name,
      "customer_staging_site": customer_staging_site,
      "customer_production_site": customer_production_site
    }
  ]
  r = requests.post(add_recipient_url, data = json.dumps(contacts), headers=header)
  if r.status_code != 201:
    print "Non-201 status code recieved: {status_code}".format(status_code=r.status_code)
    print r.text
    exit(1)
  contact_response = r.json()
  if contact_response['error_count'] != 0:
    print "Error count of {error_count}".format(error_count=contact_response['error_count'])
    exit(1)
  else:
    recipient_id = contact_response['persisted_recipients'][0]
    print "Added '{first} {last}' <{email}> to SendGrid. Recipient ID={id}".format(first=first_name, last=last_name, email=email,id=recipient_id)
  return recipient_id

def add_recipient_to_contact_list(company, recipient_id):
  # Add an existing recipient to a list
  # POST https://api.sendgrid.com/v3/contactdb/lists/{list_id}/recipients/{recipient_id}
  # Response: 201
  onefee_list_id = 173536
  newmedia_list_id = 173534
  drud_list_id = 173537
  if company == "1fee":
    list_id = onefee_list_id
  elif company == "newmedia":
    list_id = newmedia_list_id
  elif company == "drud":
    list_id = drud_list_id
  else:
    print "Unrecognized company name of '{company_name}'".format(company_name=company)
    exit(1)
  add_to_contact_list_url = 'https://api.sendgrid.com/v3/contactdb/lists/{list_id}/recipients/{recipient_id}'.format(list_id=list_id, recipient_id=recipient_id)
  r = requests.post(add_to_contact_list_url, headers=header)
  if r.status_code != 201:
    print "Non-201 status code recieved: {status_code}".format(status_code=r.status_code)
    print r.text
    exit(1)
  else:
    print "Added recipient with ID of '{id}' to the {company} mailing list.".format(id=recipient_id, company=company)

def add_sendgrid_recipient(company_name, first_name, last_name, email, customer_business_name, customer_staging_site, customer_production_site):
  recipient_id = add_recipient(first_name, last_name, email, customer_business_name, customer_staging_site, customer_production_site)
  add_recipient_to_contact_list(company_name, recipient_id)

@click.command()
@click.option('--add', 'operation', flag_value='add', default=True)
@click.option('--remove', 'operation', flag_value='remove')
@click.option('--company-name', default="newmedia", help="Which internal company is the client associated with?")
@click.option('--first-name', prompt="First Name", help="What is the client's first name?")
@click.option('--last-name', prompt="Last Name", help="What is the client's last name?")
@click.option('--email', prompt="Email Address", help="What is the client's email address?")
@click.option('--customer-business-name', prompt="Client Legal Business Name", help="Client's legal business name")
@click.option('--customer-staging-site', prompt="Staging URL", help="Client's staging URL")
@click.option('--customer-production-site', prompt="Prod URL", help="Client's prod URL")
def sendgrid_router(operation, company_name, first_name, last_name, email, customer_business_name, customer_staging_site, customer_production_site):
  if operation=="add":
    add_sendgrid_recipient(company_name, first_name, last_name, email, customer_business_name, customer_staging_site, customer_production_site)
  else:
    print "Operation '{op}' not supported".format(op=operation)
    exit(1)

# Search for a specific recipient by any field
# GET https://api.sendgrid.com/v3/contactdb/recipients/search?{field_name}=bob
if __name__ == '__main__':
  sendgrid_router()