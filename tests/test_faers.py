import math
import requests
from datetime import datetime, timezone

def fetch_count(query_params: dict) -> int:
    try:
        resp = requests.get('https://api.fda.gov/drug/event.json', params=query_params, timeout=15)
        if resp.status_code == 404:
            return 0
        resp.raise_for_status()
        return resp.json().get('meta', {}).get('results', {}).get('total', 0)
    except Exception as e:
        print(f"Failed: {e}")
        return 0

def get_signal_stats(drug: str, event: str):
    q_both = {'search': f'(patient.drug.medicinalproduct:\"{drug}\") AND (patient.reaction.reactionmeddrapt:\"{event}\")', 'limit': 1}
    a = fetch_count(q_both)
    
    if a == 0:
        return {'report_count': 0}
        
    q_total = {'limit': 1}
    q_drug = {'search': f'patient.drug.medicinalproduct:\"{drug}\"', 'limit': 1}
    q_event = {'search': f'patient.reaction.reactionmeddrapt:\"{event}\"', 'limit': 1}
    
    n_total = fetch_count(q_total)
    n_drug = fetch_count(q_drug)
    n_event = fetch_count(q_event)
    
    b = n_drug - a
    c = n_event - a
    d = n_total - a - b - c
    
    if b <= 0 or c <= 0 or d <= 0:
        return {'report_count': a, 'prr': None}
        
    prr = (a / (a + b)) / (c / (c + d))
    ror = (a / b) / (c / d)
    
    se_log_prr = math.sqrt(1/a - 1/(a+b) + 1/c - 1/(c+d))
    prr_lower_ci = math.exp(math.log(prr) - 1.96 * se_log_prr)
    
    se_log_ror = math.sqrt(1/a + 1/b + 1/c + 1/d)
    ror_lower_ci = math.exp(math.log(ror) - 1.96 * se_log_ror)
    
    return {
        'a': a, 'b': b, 'c': c, 'd': d,
        'prr': round(prr, 4), 'ror': round(ror, 4),
        'prr_lower_ci': round(prr_lower_ci, 4), 'ror_lower_ci': round(ror_lower_ci, 4)
    }

print("semaglutide, pancreatitis:", get_signal_stats("semaglutide", "pancreatitis"))
print("atorvastatin, common_cold:", get_signal_stats("atorvastatin", "common cold"))
