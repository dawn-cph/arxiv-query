"""
Run an arXiv query on a group of names and pipe results to an HTML table
"""

### Names to query
NAMES="""
toft_s
greve_t
fynbo_j
watson_d
steinhardt_c
magdis_g
brammer_g
jakobsen_p
norregaard-nielsen_h
hornstrup_a
malesani_d
selsing_j
valentino_f
ceverino_d
nakajima_k
bonaventura_n
milvang-jensen_b
stockmann_m
gomez-guijarro_c
cortzen_i
kokorev_v
killi_m
weaver_j
"""

#MIN_DATE = '2018-01-01'

def run_arxiv_query(names=NAMES, max_results=100, min_date='2018-01-01', output='dawn_arxiv', table_type='grizli', verbose=True):

    import xmltodict
    import urllib.request
   
    BASE_URL = "http://export.arxiv.org/api/query?search_query=%28{0}%29+AND+cat:astro-ph*&sortBy=submittedDate&sortOrder=descending&max_results={1}"
    authors = NAMES.strip().split()
    QUERY = BASE_URL.format('+OR+'.join(authors), max_results)

    if verbose:
        print('Run query: {0}'.format(QUERY))
    
    result = urllib.request.urlopen(QUERY).read()
    
    if verbose:
        print('Parse results')
        
    entries = xmltodict.parse(result)['feed']['entry']
    tab = entries_to_table(entries, table_type=table_type)
    
    if table_type in ['grizli','pandas']:
        sel = tab['published'] > min_date
        tab = tab[sel]
    
    if table_type == 'grizli':
        tab['url', 'date', 'title', 'author', 'comment', 'cat'].write_sortable_html(output+'.html', max_lines=max_results+1, localhost=False)
        
        tab.write(output+'.tbl', format='ascii.ipac', overwrite=True)
        if verbose:
            print('Save to {0}.html/.tbl'.format(output))
            
    elif table_type == 'pandas':
        tab[['url', 'date', 'title', 'author', 'comment', 'cat']].to_html(output+'.html', escape=False)
        print('Save to {0}.html'.format(output))
    elif table_type == 'email':
        if verbose:
            print('Parse emailer!')
            
        tab = dict_to_email(tab, min_date)
        if not tab:
            raise(IOError('No entries found for >{0}'.format(min_date)))
            
    return tab

def dict_to_email(tab, min_date):
    """
    Format into an ASCII email body
    """
    N = len(tab['id'])
    body = ""
    for i in range(N):
        item="""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
{0}   /   {1}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{2}

{3}

{4}

""".format(tab['id'][i], tab['date'][i], tab['title'][i], tab['author'][i], tab['summary'][i])
        #print(item)
        if tab['date'][i] >= min_date:
            body += item
        
    return body
    
def entries_to_table(entries, table_type='grizli'):
    """
    Parse `entries` dictionary read from the XML output into a table
    
    table_type: 'email', 'dict', 'grizli', 'pandas'
    
    """
    
    delim=['<<< ',' >>>']
    
    if table_type in ['email', 'dict']:
        from collections import OrderedDict
        tab = OrderedDict()
    elif table_type == 'grizli':
        from grizli import utils
        tab = utils.GTable()
        delim=['<b>','</b>']
    elif table_type == 'pandas':
        import pandas
        tab = pandas.DataFrame()
    else:
        print('Only "dict", "grizli", "pandas" table types understood')
        return False
        
    for key in ['id', 'published', 'title', 'summary']:
        tab[key] = [entry[key] for entry in entries]
    
    tab['author'] = [strip_authors(entry['author'], delim=delim) for entry in entries]
    
    #print(entries[0].keys()); raise(IOError)
    
    comments = []
    for entry in entries:
        if 'arxiv:comment' in entry:
            comments.append(entry['arxiv:comment']['#text'])
        else:
            comments.append('')
            
    tab['comment'] = comments
    
    tab['cat'] = [entry['arxiv:primary_category']['@term'] for entry in entries]
    tab['url'] = ['<a href={0}>{1}</a>'.format(url, url.split('/')[-1]) for url in tab['id']]
    tab['date'] = [pub[:-1].replace('T', ' ') for pub in tab['published']]
    
    return tab
    
def strip_authors(auth_dict=[{'name':'Gabriel Brammer'}], keep=3, names=NAMES, delim=['<b>','</b>']):
    last_names = [n.split('_')[0].title() for n in NAMES.strip().split()]
    #print(auth_dict)
    if isinstance(auth_dict, list):
        authors = [d['name'].split()[-1].title() for d in auth_dict]
    else:
        authors = [auth_dict['name'].split()[-1].title()]
        
    for i, a in enumerate(authors):
       if a in last_names:
           authors[i] = '{0}{1}{2}'.format(delim[0], a, delim[1])
    
    return ', '.join(authors)

def aws_emailer(names=NAMES, min_date='2018-01-01', max_results=100, SENDER='foo@aol.com', RECIPIENT='bar@aol.com', AWS_REGION = "us-east-1"):
    """
    Email tool using AWS SES
    
    https://docs.aws.amazon.com/ses/latest/DeveloperGuide/send-using-sdk-python.html
    
    """
    import time
    import boto3
    from botocore.exceptions import ClientError
    
    BODY_TEXT = run_arxiv_query(names=names, max_results=max_results, min_date=min_date, output=None, table_type='email', verbose=True)
            
    SUBJECT = 'arXiv summary: {0}'.format(time.ctime())
        
    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)
    
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            #ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
        
def handler(event, context):
    """AWS Lambda handler"""
    import time
    parsed = {}
    
    if 'min_date' in event:
        parsed['min_date'] = event['min_date']
    else:
        # 24 hours ago
        tm1 = time.gmtime(time.time()-24*60*60)
        parsed['min_date'] = '{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}Z'.format(tm1.tm_year, tm1.tm_mon, tm1.tm_mday, tm1.tm_hour, tm1.tm_min, tm1.tm_sec)
    
    if 'days_back' in event:
        tm1 = time.gmtime(time.time()-float(event['days_back'])*24*60*60)
        parsed['min_date'] = '{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}Z'.format(tm1.tm_year, tm1.tm_mon, tm1.tm_mday, tm1.tm_hour, tm1.tm_min, tm1.tm_sec)
        
    if 'max_results' in event:
        parsed['max_results'] = int(event['max_results'])
    else:
        parsed['max_results'] = 25
        
    parsed['SENDER'] = event['SENDER']
    parsed['RECIPIENT'] = event['RECIPIENT']
    
    aws_emailer(**parsed)
    
if __name__ == '__main__':
    import sys
    print(sys.argv)
    #run_arxiv_query()
    try:
        _, names_file, min_date, output = sys.argv
    except:
        print('Usage: $ python arxiv_query.py DAWN.txt 2018-10-01 dawn_arxiv')
        exit
        
    names = [l.strip() for l in open(names_file).readlines()]
     
    run_arxiv_query(names=names, max_results=100, min_date=min_date, output=output, table_type='grizli', verbose=True)
    
#http://export.arxiv.org/api/query?search_query=%28au:Brammer_G+OR+au:Toft_S%29+AND+cat:astro-ph*&sortBy=lastUpdatedDate&sortOrder=descending