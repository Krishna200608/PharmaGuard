with open('docs/context/DECISIONS.md', 'r', encoding='utf-8') as f:
    content = f.read()

new_section = """## 1.1 MoA Curation Methodology (Anti-Circularity Rule)
**Decision:** Mechanism of Action (MoA) text must be authored or reviewed strictly for general pharmacology WITHOUT looking at which adverse event it will be evaluated against. General pharmacology is written first, and only paired with `ground_truth.json` afterward.
**Why:** Prevents data leakage/circularity. If an adverse-event-specific mechanism (e.g., "causes mitochondrial dysfunction" for hepatotoxicity) is planted directly into the MoA field, the LLM isn't independently reasoning from general pharmacology—it's just being handed the answer.

"""

content = content.replace("## 2. Plausibility Default", new_section + "## 2. Plausibility Default")

with open('docs/context/DECISIONS.md', 'w', encoding='utf-8') as f:
    f.write(content)
