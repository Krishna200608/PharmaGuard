# Third-Party Notices & Data Licensing

This document details the third-party datasets, pharmacological registries, and external reference materials distributed within the PharmaGuard repository (`pharmaguard/data/`).

While the core PharmaGuard software, agent orchestration, evaluation harnesses, and documentation are licensed under the [MIT License](LICENSE), certain data files are derived from external open-science resources and are subject to their respective upstream licenses as specified below.

---

## 1. ChEMBL Database Registry (`pharmaguard/data/chembl_lookup.json`)

* **Upstream Resource:** [EMBL-EBI ChEMBL Bioactivity & Drug Target Database](https://www.ebi.ac.uk/chembl/)
* **Upstream Provider:** European Molecular Biology Laboratory - European Bioinformatics Institute (EMBL-EBI)
* **Release Version Used:** ChEMBL REST API v34
* **Upstream License:** [Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)](https://creativecommons.org/licenses/by-sa/3.0/)
* **License Notice & ShareAlike Restriction:**
  `pharmaguard/data/chembl_lookup.json` contains curated compound identifiers, mechanism-of-action descriptions, target names, and target classifications derived from the ChEMBL database. In accordance with the CC BY-SA 3.0 ShareAlike term, **this specific data file is NOT covered by PharmaGuard's MIT License**; it remains licensed under CC BY-SA 3.0. Any redistribution or modification of this file must carry the same or a compatible ShareAlike license.
* **Required Academic Attribution:**
  > Gaulton, A., Bellis, L. J., Bento, A. P., Chambers, J., Davies, M., Hersey, A., ... & Overington, J. P. (2012). ChEMBL: a large-scale bioactivity database for drug discovery. *Nucleic Acids Research*, 40(D1), D1100–D1107. [DOI: 10.1093/nar/gkr777](https://doi.org/10.1093/nar/gkr777).
  >
  > Mendez, D., Gaulton, A., Bento, A. P., Chambers, J., De Veij, M., Félix, E., ... & Leach, A. R. (2019). ChEMBL: towards direct deposition of bioassay data. *Nucleic Acids Research*, 47(D1), D930–D940. [DOI: 10.1093/nar/gky1075](https://doi.org/10.1093/nar/gky1075).

---

## 2. OMOP Pharmacovigilance Reference Set (`pharmaguard/data/external/omopReferenceSet.rda` & `ground_truth_omop_pilot.json`)

* **Upstream Resource:** [OHDSI MethodEvaluation](https://github.com/OHDSI/MethodEvaluation) R Package
* **Upstream Provider:** Observational Health Data Sciences and Informatics (OHDSI)
* **Source Archive:** [omopReferenceSet.rda](https://raw.githubusercontent.com/OHDSI/MethodEvaluation/master/data/omopReferenceSet.rda)
* **Copyright:** Copyright © Observational Health Data Sciences and Informatics (OHDSI)
* **Upstream License:** [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
* **Apache 2.0 Attribution Notice:**
  Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at `http://www.apache.org/licenses/LICENSE-2.0`.
  Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
* **Modifications:**
  * `pharmaguard/data/external/omopReferenceSet.rda`: Unmodified binary R Data Archive (XZ-compressed, 6,872 bytes) containing 399 reference drug-outcome pairs.
  * `pharmaguard/data/ground_truth_omop_pilot.json`: A derived subset of 32 generic drug-outcome pairs parsed from `omopReferenceSet.rda`, standardized into PharmaGuard's JSON ground-truth benchmark schema.
* **Required Academic Attribution:**
  > Ryan, P. B., Schuemie, M. J., Welebob, E., Duke, J., Valentine, S., & Hartzema, A. G. (2013). Defining a ground truth for pharmacovigilance signal detection: the OMOP labeled drug and adverse event test set. *Drug Safety*, 36(Suppl 1), S33–S47. [DOI: 10.1007/s40264-013-0097-8](https://doi.org/10.1007/s40264-013-0097-8).

---

## 3. U.S. FDA Regulatory Data & Public Records (`pharmaguard/data/ground_truth.json`)

* **Upstream Source:** U.S. Food and Drug Administration (FDA) Drug Safety Communications, Approved Drug Labeling (package inserts via `accessdata.fda.gov`), Boxed Warnings, and Risk Evaluation and Mitigation Strategies (REMS).
* **Copyright Status:** Works of the United States Government. Under Section 105 of the Copyright Act (17 U.S.C. § 105), works produced by officers or employees of the U.S. Government as part of their official duties are in the **public domain** within the United States.
* **Bibliographic Citations:** URL links, PMIDs, and DOIs provided in `ground_truth.json` are factual citations to public government records and published medical literature, non-restrictive of redistribution.

---

## 4. Human-Curated Plausibility Ratings (`pharmaguard/data/plausibility_ratings.json`)

* **Authorship:** Authored and curated by Krishna Sikheriya for the PharmaGuard research project under the rubric defined in `pharmaguard/prompts/evidence_grading_rubric.txt`.
* **Licensing:** The written mechanistic rationales and structured ratings are original works of the PharmaGuard project and are licensed under PharmaGuard's top-level [MIT License](LICENSE).
* **Referenced Identifiers:** Entries cross-reference factual ChEMBL Compound IDs (`CHEMBL*`) to maintain reproducibility with the ChEMBL database.
