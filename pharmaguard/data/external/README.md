# External Datasets

This directory contains external benchmark datasets and reference files used by PharmaGuard.

## 1. OMOP Reference Set (`omopReferenceSet.rda`)
- **Source:** OHDSI MethodEvaluation R package (`OHDSI/MethodEvaluation`)
- **Source URL:** [https://raw.githubusercontent.com/OHDSI/MethodEvaluation/master/data/omopReferenceSet.rda](https://raw.githubusercontent.com/OHDSI/MethodEvaluation/master/data/omopReferenceSet.rda)
- **Reference Publication:** Ryan PB, Schuemie MJ, Welebob E, Duke J, Valentine S, Hartzema AG. *Defining a Ground Truth for Pharmacovigilance Signal Detection*. Drug Safety (2013) 36(Suppl 1):S33–S47. DOI: [10.1007/s40264-013-0097-8](https://doi.org/10.1007/s40264-013-0097-8).
- **Format:** R Data Archive (`.rda`) XZ-compressed (6,872 bytes).
- **Contents:** 399 drug-outcome reference pairs across 4 clinical endpoints (Acute Liver Failure, Acute Renal Failure, Acute Myocardial Infarction, Upper GI Bleeding) with designated positive and negative controls.
- **Repository Usage:** Parsed via `pyreadr` to derive the 32 generic drug pairs evaluated in `pharmaguard/data/ground_truth_omop_pilot.json`.
