"""
Run an arXiv query on a group of names and pipe results to an HTML table
"""

### Names to query
NAMES="""
brammer_g
toft_s
magdis_g
steinhardt_c
watson_d
greve_t
fynbo_j
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
        
    return tab
    
def entries_to_table(entries, table_type='grizli'):
    """
    Parse `entries` dictionary read from the XML output into a table
    
    table_type: 'dict', 'grizli', 'pandas'
    
    """
    if table_type == 'dict':
        from collections import OrderedDict
        tab = OrderedDict()
        
    elif table_type == 'grizli':
        from grizli import utils
        tab = utils.GTable()
    elif table_type == 'pandas':
        import pandas
        tab = pandas.DataFrame()
    else:
        print('Only "dict", "grizli", "pandas" table types understood')
        return False
        
    for key in ['id', 'published', 'title']:
        tab[key] = [entry[key] for entry in entries]
    
    tab['author'] = [strip_authors(entry['author']) for entry in entries]
    
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
    
def strip_authors(auth_dict=[{'name':'Gabriel Brammer'}], keep=3, names=NAMES):
    last_names = [n.split('_')[0].title() for n in NAMES.strip().split()]
    #print(auth_dict)
    if isinstance(auth_dict, list):
        authors = [d['name'].split()[-1].title() for d in auth_dict]
    else:
        authors = [auth_dict['name'].split()[-1].title()]
        
    for i, a in enumerate(authors):
       if a in last_names:
           authors[i] = '<b>{0}</b>'.format(a)
    
    return ', '.join(authors)

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