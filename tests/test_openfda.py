import requests

def get_count(q):
    r = requests.get('https://api.fda.gov/drug/event.json', params=q)
    return r.json().get('meta', {}).get('results', {}).get('total', 0) if r.status_code == 200 else 0

print('total:', get_count({}))
print('drug:', get_count({'search': 'patient.drug.medicinalproduct:"semaglutide"'}))
print('event:', get_count({'search': 'patient.reaction.reactionmeddrapt:"pancreatitis"'}))
print('both:', get_count({'search': '(patient.drug.medicinalproduct:"semaglutide") AND (patient.reaction.reactionmeddrapt:"pancreatitis")'}))
