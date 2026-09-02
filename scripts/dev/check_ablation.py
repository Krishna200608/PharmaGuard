# Historical diagnostic script for checking ablation study agreement against curated references (not part of the maintained pipeline).
import json, os, glob

files = glob.glob('outputs/experiments/ablation/*.json')
agreements = 0
disagreements = []

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
    pair = f"{data.get('drug')} + {data.get('event')}"
    chembl = data.get('mechanism', {})
    source = chembl.get('plausibility_source')
    level = chembl.get('biological_plausibility')
    curated = chembl.get('curated_reference')
    rationale = chembl.get('plausibility_rationale')
    
    if level == curated:
        agreements += 1
    else:
        disagreements.append((pair, curated, level, rationale))

print(f'Total: {len(files)}')
print(f'Agreement: {agreements}/{len(files)} ({agreements/len(files)*100:.1f}%)')
for d in disagreements:
    print(f'Disagreement: {d[0]}')
    print(f'  Curated: {d[1]} | Agent: {d[2]}')
    print(f'  Rationale: {d[3]}')
    print('-'*40)