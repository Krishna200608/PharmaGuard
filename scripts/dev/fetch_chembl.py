# Developer utility for querying ChEMBL API to populate chembl_lookup.json from ground truth pairs (not part of the maintained pipeline).
import json
import requests
import time
from pathlib import Path

DATA_DIR = Path("pharmaguard/data")
CHEMBL_LOOKUP = DATA_DIR / "chembl_lookup.json"
GROUND_TRUTH = DATA_DIR / "ground_truth.json"

with open(CHEMBL_LOOKUP, "r", encoding="utf-8") as f:
    lookup_data = json.load(f)
drugs = lookup_data.setdefault("drugs", {})

with open(GROUND_TRUTH, "r", encoding="utf-8") as f:
    gt_data = json.load(f)

missing = set()
for pair in gt_data["pairs"]:
    d = pair["drug_canonical"].lower()
    if d not in drugs:
        missing.add(d)

print(f"Missing drugs: {missing}")

for d in missing:
    print(f"Fetching {d}...")
    resp = requests.get(f"https://www.ebi.ac.uk/chembl/api/data/molecule.json?pref_name__iexact={d}")
    if resp.status_code != 200:
        print(f"Failed to fetch {d}: {resp.status_code}")
        continue
    data = resp.json()
    mols = data.get("molecules", [])
    if not mols:
        print(f"No results for {d}")
        continue
    
    mol = mols[0]
    chembl_id = mol["molecule_chembl_id"]
    pref_name = mol.get("pref_name", d)
    
    # fetch mechanisms
    mech_resp = requests.get(f"https://www.ebi.ac.uk/chembl/api/data/mechanism.json?molecule_chembl_id={chembl_id}")
    mechs = mech_resp.json().get("mechanisms", [])
    if mechs:
        mech = mechs[0]
        moa = mech.get("mechanism_of_action", "")
        target_name = mech.get("target_dict", {}).get("pref_name", "")
    else:
        moa = "Unknown"
        target_name = "Unknown"

    drugs[d] = {
        "chembl_id": chembl_id,
        "canonical_name": pref_name,
        "trade_names": [],
        "mechanism_of_action": moa,
        "target_name": target_name,
        "target_class": "Unknown",
        "resolved_at": "2026-08-11",
        "chembl_url": f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/"
    }
    time.sleep(1)

with open(CHEMBL_LOOKUP, "w", encoding="utf-8") as f:
    json.dump(lookup_data, f, indent=2)

print("Updated chembl_lookup.json")