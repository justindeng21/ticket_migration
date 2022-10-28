import requests 
import json
import ticket
from ticket import create_ticket_dictionary

def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key).replace("\n"," "))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value).replace("\n"," \ "))



def main():
    tickets, case_ids = create_ticket_dictionary()

    headers = {'content-type': 'application/json'}
    url = 'https://crownpeaksupport1663789408.zendesk.com/api/v2/imports/tickets/create_many'


    ticket_payload = []


    for i in range(len(tickets)):
        ticket_payload.append(tickets[case_ids[i]].construct_payload()['ticket'])

    data = {'tickets':ticket_payload}
    payload = json.dumps(data)

    #with open("../data/sample.json", "w") as outfile:
    #    outfile.write(payload)
    

    

    response = requests.post(url, data=payload, auth=(ticket.user, ticket.pwd), headers=headers)

    print('Import response: ',response.status_code)
    
main()

