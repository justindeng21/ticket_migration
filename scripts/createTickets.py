import pandas
import requests 
import json

user = '-'
pwd = '-'

def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key).replace("\n"," "))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value).replace("\n"," \ "))


comments_data = pandas.read_csv('../data/comments.csv')
cases_data = pandas.read_csv('../data/cases.csv')
attachments_data = pandas.read_csv('../data/attachments.csv')

def zendesk_query(query):
    
    url = 'https://crownpeaksupport1663789408.zendesk.com/api/v2/users/search.json?query=' + query
    response = requests.get(url, auth=(user, pwd))

    if response.status_code != 200:
        exit()

    return response.json()['users'][0]['id'], response.json()['users'][0]['email']


def fetch_user_data(cases):

    user_ids = {}
    for index, row_case in cases.iterrows():
        
        try:
            if row_case['Case Owner'].split('@')[1] == 'e-spirit.com' or row_case['Case Owner'].split('@')[1] == 'crownpeak.com':
                query = row_case['Case Owner'].split('@')[0]+'@test.com'
        except:
            query = row_case['Case Owner']
        
        user_id, user_email = zendesk_query(query)
        user_ids[user_email] = user_id


    for index, row_case in cases.iterrows():

        try:
            if row_case['Contact: Email'].split('@')[1] == 'llbean.com':
                query = row_case['Contact: Email'].split('@')[0]+'@fake.com'
        except:
            query = row_case['Contact: Email']
        
        user_id, user_email = zendesk_query(query)
        user_ids[user_email] = user_id
        

    return user_ids

user_ids = fetch_user_data(cases_data)






class Ticket:
    def __init__(self, case):
        self.case = case
        self.comments = []
        self.attachments = []
        return

    #   attachments

    def add_attachment(self,attachment):
        self.attachments.append(attachment)
        return

    def get_attachments(self):
        return self.attachments

    #   comments

    def add_comment(self,comment):
        self.comments.append(comment)
        return

    def get_comments(self):
        return self.comments

    #

    def get_payload(self):
        return self.payload
    
    def get_case_col(self,column_name):         #returns the column specified in paramerters
        return self.case[column_name]

    def get_case_details(self):
        return self.case
    #

    def date_split(self):
        date_raw = self.get_case_col('Date/Time Closed')


        date_arr = date_raw.split('/')
        year = date_arr[2].split(' ')[0]
        if len(date_arr[0]) == 1:
            date_arr[0] = '0'+date_arr[0]

        if len(date_arr[1]) == 1:
            date_arr[1] = '0'+date_arr[1]

        date = year + '-' + date_arr[0] + '-' + date_arr[1]
        return date


    #

    def date_split_2(self):
        date_raw = self.get_case_col('Date/Time Opened')

        date_arr = date_raw.split('/')

        year = date_arr[2].split(' ')[0]

        if len(date_arr[0]) == 1:
            date_arr[0] = '0'+date_arr[0]

        if len(date_arr[1]) == 1:
            date_arr[1] = '0'+date_arr[1]

        time = date_arr[2].split(' ')[1]

        if len(time) == 7:
            time = '0'+ time

        time = '00:00:00'

        date = year + '-' + date_arr[0] + '-' + date_arr[1] + 'T'+ time +'Z'
        return date

    def construct_payload(self):
        date = self.date_split()
        jira_id = '' 
        version = ''
        component = ''
        description = ''
        if  pandas.notna(self.get_case_col('JIRA Id')) == True:
            jira_id = self.get_case_col('JIRA Id')

        if pandas.notna(self.get_case_col('Version')) == True:
            version = self.get_case_col('Version')
        
        if pandas.notna(self.get_case_col('Component') == True and self.get_case_col('Component') != ' '):
            component = self.get_case_col('Component').lower().replace(' ','_')

        if pandas.notna(self.get_case_col('Description') == True):
            description = self.get_case_col('Description')

        attachments = self.get_attachments()
        attachment_tokens = []

        for attachment in attachments:
            case_id = attachment.get_attachment_col('Case ID')
            filename ='../attachments/'+case_id+'_'+attachment.get_attachment_col('filename')
            url = 'https://crownpeaksupport1663789408.zendesk.com/api/v2/uploads.json?filename=' + filename
            params = {'filename': filename}
            upload_headers = {'content-type': 'application/binary'}

            with open(filename,'rb') as file:
                response = requests.post(url,params=params,data=file,auth=(user,pwd),headers=upload_headers) 


            data = response.json()
            attachment_tokens.append(data['upload']['token'])


        comments = self.get_comments()
        comments_ = []


        internal_comment_value = "**Legacy ID:** " + self.get_case_col('Case ID') + '\n' + self.get_case_col('Case URL (formula)')

        if jira_id != '':
            internal_comment_value += '\n' + '**JIRA ID:** ' + jira_id + '\n' + 'https://jira.crownpeak.com/browse/' + jira_id


        internal_comment = {
            
            "author_id": '7431029297309',
            "value": internal_comment_value,
            "public": 'false'
        }

        attachment_commet = {
            "author_id": '7431029297309',
            "value":"Attachments for "+self.get_case_col('Case ID'),
            "uploads": attachment_tokens
        }

        description_comment = {
            "author_id": '7431029297309',
            "created_at": self.date_split_2(),
            "value":"**Description:** " + description
            
        }




        comments_.append(description_comment)
        comments_.append(internal_comment)

        if len(attachment_tokens) != 0:
            comments_.append(attachment_commet)

        for comment_data in comments:
            
            try:
                if comment_data.get_comment_col('Case Comment Created By').split('@')[1] =="e-spirit.com" or comment_data.get_comment_col('Case Comment Created By').split('@')[1] =="crownpeak.com":
                    user_ = comment_data.get_comment_col('Case Comment Created By').split('@')[0]+'@test.com'
                else:
                    user_ = comment_data.get_comment_col('Case Comment Created By').split('@')[0]+'@fake.com'
            except:
                user_ = comment_data.get_comment_col('Case Comment Created By')
            
            try:
                id = user_ids[user_]

            except:
                id, email = zendesk_query(user_)

            comment =  {
                "author_id": id,
                "created_at": comment_data.date_split(),
                "value":"**Comment:** "+ comment_data.get_comment_col('Case Comments')
                }

            comments_.append(comment)




        assignee_id = 0
        requester_id = 0
        try:
            assignee_id = user_ids[self.get_case_col('Case Owner').split('@')[0]+'@test.com']
        except:
            assignee_id,email = zendesk_query(self.get_case_col('Case Owner'))


        try:
            requester_id = user_ids[self.get_case_col('Contact: Email').split('@')[0]+'@fake.com']
        except:
            assignee_id,email = zendesk_query(self.get_case_col('Contact: Email'))

        
        case_data = {
            'ticket': {
                'assignee_id':assignee_id,
                'comments':comments_,
                'subject': self.get_case_col('Subject'),
                'requester_id':requester_id,
                'priority':self.get_case_col('Priority').lower(),
                'status': 'open',
                'custom_fields': [
                    {'id':7247394363293, 'value': self.get_case_col('Case Reason').lower().replace(' ','_')},             #case reason

                    {'id':7247354654493, 'value': self.get_case_col('Type').lower().replace(' ','_')},                   #firstspiritproduct

                    {'id':7247320492957, 'value': 'firstspirit'},                     #product line

                    {'id':6845150379677, 'value': component},                         #firstspirit component

                    {'id':7247465821981, 'value': jira_id},                           #JIRA ID

                    {'id':7247465380893, 'value': self.get_case_col('Case ID')},      #Legacy ticket ID

                    {'id':7247359071901, 'value': version},                           #product version

                    {'id':7247436551581, 'value': date}                               #date


                                ]
                }}
        self.payload = case_data




        
        return self.payload


class Comment:
    def __init__(self, comment):
        self.comment = comment
        return

    def get_comment_col(self,column_name):
        return self.comment[column_name]

    def date_split(self):
        
        date_raw = self.get_comment_col('Case Comment Created Date')

        date_arr = date_raw.split('/')

        year = date_arr[2].split(' ')[0]

        if len(date_arr[0]) == 1:
            date_arr[0] = '0'+date_arr[0]

        if len(date_arr[1]) == 1:
            date_arr[1] = '0'+date_arr[1]

        time = date_arr[2].split(' ')[1]

        if len(time) == 4:
            time = '0'+ time

        time  = time+':00'

        date = year + '-' + date_arr[0] + '-' + date_arr[1] + 'T'+ time +'Z'
        return date

class Attachment:
    def __init__(self, Attachment):
        self.Attachment = Attachment
        return

    def get_attachment_col(self,column_name):
        return self.Attachment[column_name]



def create_ticket_dictionary(cases_, comments_, attachments_):
    ticket_dictionary = {}
    case_ids =[]

    for index, row_case in cases_.iterrows():
        current_ticket_id = row_case['Case ID']
        ticket = Ticket(row_case)
        ticket_dictionary[current_ticket_id] = ticket
        case_ids.append(current_ticket_id)


    for index, row_comment in comments_.iterrows():
        current_ticket_id = row_comment['Case ID']
        comment = Comment(row_comment)
        ticket_dictionary[current_ticket_id].add_comment(comment)
        
        
    for index, row_attachment in attachments_.iterrows():
        current_ticket_id = row_attachment['Case ID']
        attachment = Attachment(row_attachment)
        ticket_dictionary[current_ticket_id].add_attachment(attachment)
        

    return ticket_dictionary,case_ids


def main():
    tickets, case_ids = create_ticket_dictionary(cases_data,comments_data,attachments_data)

    headers = {'content-type': 'application/json'}
    url = 'https://crownpeaksupport1663789408.zendesk.com/api/v2/imports/tickets/create_many'


    ticket_payload = []


    for i in range(len(tickets)):
        ticket_payload.append(tickets[case_ids[i]].construct_payload()['ticket'])

    data = {'tickets':ticket_payload}
    payload = json.dumps(data)

    with open("sample.json", "w") as outfile:
        outfile.write(payload)
    

    

    response = requests.post(url, data=payload, auth=(user, pwd), headers=headers)

    print('Import response: ',response.status_code)
    


    
    

main()

