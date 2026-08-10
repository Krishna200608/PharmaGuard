# Ground Truth Candidates (Sprint 3, Part 1)

*This file serves as a durable record of the ground truth evaluation curation process.*

The following 15 curated drug-event pairs are proposed for `ground_truth.json`. Each includes a strict category, expected escalation, and a verifiable source URL.

## 🔴 Confirmed Positive Signals (7 Pairs)
*Category: `confirmed_positive`*
*Expected Escalation: `ESCALATE`*

1. **montelukast + suicidal_ideation**
   - **Source**: [FDA Boxed Warning (2020)](https://www.fda.gov/drugs/drug-safety-and-availability/fda-requires-boxed-warning-about-serious-mental-health-side-effects-asthma-and-allergy-drug)
   - **Note**: Clear boxed warning based on FAERS data and mechanistic review.

2. **ciprofloxacin + tendon_rupture**
   - **Source**: [FDA Drug Safety Communication (2008)](https://www.fda.gov/drugs/postmarket-drug-safety-information-patients-and-providers/fda-drug-safety-communication-fda-updates-warnings-many-fluoroquinolone-antibacterial-drugs)
   - **Note**: The quintessential fluoroquinolone safety signal.

3. **isotretinoin + teratogenicity**
   - **Source**: [FDA iPLEDGE REMS Program](https://www.fda.gov/drugs/postmarket-drug-safety-information-patients-and-providers/ipledge-risk-evaluation-and-mitigation-strategy-rems)
   - **Note**: Extremely strict REMS program globally known for this specific event.

4. **clozapine + agranulocytosis**
   - **Source**: [FDA Clozapine REMS](https://www.fda.gov/drugs/drug-safety-and-availability/fda-modifies-clozapine-risk-evaluation-and-mitigation-strategy-rems)
   - **Note**: Classic textbook example requiring severe monitoring.

5. **valproic_acid + hepatotoxicity**
   - **Source**: [FDA Depakote Label Boxed Warning (PDF)](https://www.accessdata.fda.gov/drugsatfda_docs/label/2021/018723s059,019680s046lbl.pdf)
   - **Note**: Explicit black box warning.

6. **rosiglitazone + myocardial_infarction**
   - **Source**: [FDA Avandia Safety Review](https://www.fda.gov/drugs/drug-safety-and-availability/fda-drug-safety-communication-fda-requires-removal-some-prescribing-and-dispensing-restrictions)
   - **Note**: Boxed warning was relaxed in 2013, but the initial signal in FAERS/literature is a famous pharmacovigilance case study.

7. **pembrolizumab + pneumonitis**
   - **Source**: [Keytruda FDA Label (PDF)](https://www.accessdata.fda.gov/drugsatfda_docs/label/2021/125514s096lbl.pdf)
   - **Note**: Hallmark immune-mediated adverse effect of PD-1 inhibitors.

---

## 🟢 Genuine Negative Controls (5 Pairs)
*Category: `genuine_negative_control`*
*Expected Escalation: `DO_NOT_ESCALATE`*

8. **liraglutide + pancreatic_cancer**
   - **Source**: [Egan et al., NEJM 2014](https://www.nejm.org/doi/full/10.1056/NEJMp1314078)
   - **Note**: FDA and EMA jointly assessed and dismissed the pancreatic cancer signal, concluding no causal association in a definitive, uncontested statement.

9. **metformin + hypoglycemia**
   - **Source**: [Glucophage FDA Label (PDF)](https://www.accessdata.fda.gov/drugsatfda_docs/label/2017/020357s037s039,021202s021s023lbl.pdf)
   - **Note**: Label states: "Hypoglycemia does not occur in patients receiving metformin alone". The FAERS reports are confounded by concomitant insulin/sulfonylurea use.

10. **atorvastatin + dementia**
    - **Source**: [AHA/ACC Scientific Statement (2018)](https://www.ahajournals.org/doi/10.1161/ATV.0000000000000073)
    - **Note**: FDA's 2012 safety communication noted cognitive impairment reports, but rigorous subsequent reviews concluded no causal link exists between statins and dementia.

11. **albuterol + suicidal_ideation**
    - **Source**: [FDA ProAir HFA Label (PDF)](https://www.accessdata.fda.gov/drugsatfda_docs/label/2019/021457s035lbl.pdf)
    - **Note**: Replaced `saxagliptin+influenza`. This uses the "structurally implausible mechanism" logic applied to a confirmed positive (`montelukast+suicidal_ideation`). Albuterol is an inhaled beta-2 agonist asthma drug lacking any neuropsychiatric boxed warning.

12. **amoxicillin + tendon_rupture**
    - **Source**: [Macellari et al. 2021 (PubMed)](https://pubmed.ncbi.nlm.nih.gov/34217117/)
    - **Note**: Used clinically as an active negative control in studies examining fluoroquinolone-induced tendon rupture.

---

## ⚪ Zero-Report Edge Cases (3 Pairs)
*Category: `zero_report_edge_case`*
*Expected Escalation: `DO_NOT_ESCALATE`*

13. **atorvastatin + common_cold**
    - **Source**: N/A (Synthetic test case)
    - **Note**: Used successfully in our Sprint 2 pilot test (returned exactly 0 openFDA reports and triggered the short-circuit).

14. **imatinib + tooth_eruption**
    - **Source**: N/A (Synthetic test case)
    - **Note**: Adult oncology drug paired with a pediatric developmental event. Extremely unlikely to have FAERS reports.

15. **adalimumab + frostbite**
    - **Source**: N/A (Synthetic test case)
    - **Note**: An immunosuppressant paired with an environmental injury. Tests the zero-count logic.
