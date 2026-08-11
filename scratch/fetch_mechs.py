import requests

def search(cid):
    resp = requests.get(f'https://www.ebi.ac.uk/chembl/api/data/mechanism.json?molecule_chembl_id={cid}')
    print(f'=== {cid} ===')
    for m in resp.json().get('mechanisms', []):
        moa = m.get('mechanism_of_action', '')
        action = m.get('action_type', '')
        target = m.get('target_dict', {}).get('pref_name', '')
        print(f'- {moa} (Action: {action}, Target: {target})')

search('CHEMBL109') # valproic acid
search('CHEMBL42') # clozapine
search('CHEMBL787') # montelukast
search('CHEMBL941') # imatinib
search('CHEMBL3137343') # pembrolizumab
search('CHEMBL1201580') # adalimumab
