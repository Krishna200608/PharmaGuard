# PharmaGuard Reproducibility & Provenance Manifest

**Generated:** `2026-08-30T11:37:37.842479+00:00`  
**Repository HEAD Commit:** `22e5f04c12008039139d030683a0a30f8ae80880`  
**Total Artifacts Indexed:** `75`  
**Active Tool Cache Schema:** `v7`  

---

## 1. Executive Summary & Provenance Health

This manifest indexes every evaluation, diagnostic probe, and research experiment artifact in the repository. Missing fields in legacy frozen artifacts are recorded as explicit nulls rather than backfilled with estimates.

| Provenance Completeness | Artifact Count | Percentage | Description |
| :--- | :---: | :---: | :--- |
| **COMPLETE** | **5** | **6.67%** | All 6 core fields present (`commit`, `timestamp`, `model`, `prompts`, `cache_schema`, `config_snapshot`) |
| **PARTIAL** | **66** | **88.0%** | Partial provenance (frozen run reports with `run_id`, `timestamp`, `prompts_version`) |
| **MINIMAL** | **4** | **5.33%** | Legacy probe / audit artifacts with raw metrics only |
| **TOTAL** | **75** | **100.0%** | Comprehensive index of all JSON outputs |

---

## 2. Provenance Breakdown by Artifact Type

| Artifact Type | Broad Category | Total | Complete | Partial | Minimal | Missing Fields Pattern |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `ablation_report` | `evaluation_run` | 15 | 0 | 15 | 0 | `git_commit_hash, model_name, cache_schema_version, config_snapshot` |
| `agent_agreement_audit` | `evaluation_run` | 1 | 0 | 0 | 1 | `git_commit_hash, timestamp, model_name, prompts_version, cache_schema_version, config_snapshot` |
| `baseline_report` | `evaluation_run` | 15 | 0 | 15 | 0 | `git_commit_hash, model_name, cache_schema_version, config_snapshot` |
| `confounding_probe_report` | `diagnostic_probe` | 1 | 0 | 1 | 0 | `git_commit_hash, model_name, cache_schema_version, config_snapshot` |
| `confounding_self_probe` | `diagnostic_probe` | 1 | 0 | 0 | 1 | `git_commit_hash, timestamp, model_name, prompts_version, cache_schema_version, config_snapshot` |
| `critic_probe_results` | `diagnostic_probe` | 1 | 0 | 0 | 1 | `git_commit_hash, timestamp, model_name, prompts_version, cache_schema_version, config_snapshot` |
| `diagnostic_probe_report` | `diagnostic_probe` | 3 | 0 | 3 | 0 | `git_commit_hash, model_name, cache_schema_version, config_snapshot` |
| `production_report` | `production_benchmark` | 15 | 0 | 15 | 0 | `git_commit_hash, model_name, cache_schema_version, config_snapshot` |
| `react_agent_report` | `evaluation_run` | 15 | 0 | 15 | 0 | `git_commit_hash, model_name, cache_schema_version, config_snapshot` |
| `reproducibility_manifest` | `meta_manifest` | 1 | 0 | 1 | 0 | `model_name, prompts_version, config_snapshot` |
| `research_ablation_experiment` | `research_experiment` | 3 | 3 | 0 | 0 | `None (Fully specified)` |
| `research_stability_experiment` | `research_experiment` | 2 | 2 | 0 | 0 | `None (Fully specified)` |
| `research_taxonomy_experiment` | `research_experiment` | 1 | 0 | 1 | 0 | `git_commit_hash, model_name, prompts_version, cache_schema_version, config_snapshot` |
| `stability_analysis` | `stability_evaluation` | 1 | 0 | 0 | 1 | `git_commit_hash, timestamp, model_name, prompts_version, cache_schema_version, config_snapshot` |

---

## 3. Provenance Architecture & Historical Evolution

PharmaGuard's provenance tracking evolved across three distinct architectural phases:

1. **Phase 1: Frozen Postmarketing Evaluation Reports (August 14–21, 2026)**
   - **Files:** `outputs/eval-run-*_report.json`, `outputs/baseline/`, `outputs/ablation/`, `outputs/react_agent/` (60 files)
   - **Fields Present:** `run_id`, `timestamp`, `prompts_version` (`v1.0`), `schema_version` (`1.1`).
   - **Missing Fields:** `git_commit_hash`, `model_name`, `cache_schema_version`, `config_snapshot`.
   - **Design Rationale:** These frozen evaluation reports predate the formal configuration snapshotting convention introduced in R0. Per project integrity rules, these files remain immutable.

2. **Phase 2: Diagnostic Safety Probes & Audits (August 20–27, 2026)**
   - **Files:** `outputs/critic_probe/`, `outputs/confounding_probe/`, `outputs/probe/`, `outputs/stability/loo_analysis.json` (8 files)
   - **Characteristics:** Focused on internal probe cases and post-hoc qualitative audits; metrics were output without standardized experiment metadata wrappers.

3. **Phase 3: Formal R0 & R1 Research Experiments (August 28–30, 2026)**
   - **Files:** `outputs/research/stability/*.json`, `outputs/research/source_ablation/*.json` (5 files)
   - **Fields Present:** `experiment_id`, `git_commit_hash`, `timestamp`, `model_name` (`gemini-3.1-flash-lite`), `prompts_version` (`v1.1`), `cache_schema_version` (`v7`), `config_snapshot`.
   - **Completeness:** 100% complete provenance specification with reproducible hyperparameter and cache tracking.

---

## 4. Complete Queryable Artifact Index

| Artifact Path | Type | Status | Git Commit | Timestamp | Prompts | Cache | Notes |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: | :--- |
| [`outputs/ablation/eval-run-0-montelukast-suicidal_ideation_report.json`](outputs/ablation/eval-run-0-montelukast-suicidal_ideation_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:02:52 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-1-ciprofloxacin-tendon_rupture_report.json`](outputs/ablation/eval-run-1-ciprofloxacin-tendon_rupture_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:02:57 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-10-albuterol-suicidal_ideation_report.json`](outputs/ablation/eval-run-10-albuterol-suicidal_ideation_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:03:12 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-11-amoxicillin-tendon_rupture_report.json`](outputs/ablation/eval-run-11-amoxicillin-tendon_rupture_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:03:12 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-12-atorvastatin-common_cold_report.json`](outputs/ablation/eval-run-12-atorvastatin-common_cold_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:03:15 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-13-imatinib-tooth_eruption_report.json`](outputs/ablation/eval-run-13-imatinib-tooth_eruption_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:03:16 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-14-adalimumab-frostbite_report.json`](outputs/ablation/eval-run-14-adalimumab-frostbite_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:03:16 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-2-isotretinoin-teratogenicity_report.json`](outputs/ablation/eval-run-2-isotretinoin-teratogenicity_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:02:58 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-3-clozapine-agranulocytosis_report.json`](outputs/ablation/eval-run-3-clozapine-agranulocytosis_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:02:58 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-4-valproic_acid-hepatotoxicity_report.json`](outputs/ablation/eval-run-4-valproic_acid-hepatotoxicity_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:02:59 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-5-rosiglitazone-myocardial_infarction_report.json`](outputs/ablation/eval-run-5-rosiglitazone-myocardial_infarction_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:02:59 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-6-pembrolizumab-pneumonitis_report.json`](outputs/ablation/eval-run-6-pembrolizumab-pneumonitis_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:03:02 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-7-liraglutide-pancreatic_cancer_report.json`](outputs/ablation/eval-run-7-liraglutide-pancreatic_cancer_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:03:04 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-8-metformin-hypoglycaemia_report.json`](outputs/ablation/eval-run-8-metformin-hypoglycaemia_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:03:04 | `v1.0` | — | Frozen execution report |
| [`outputs/ablation/eval-run-9-atorvastatin-dementia_report.json`](outputs/ablation/eval-run-9-atorvastatin-dementia_report.json) | `ablation_report` | **PARTIAL** | — | 2026-08-14T12:03:09 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-0-montelukast-suicidal_ideation_report.json`](outputs/baseline/eval-run-0-montelukast-suicidal_ideation_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:04:30 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-1-ciprofloxacin-tendon_rupture_report.json`](outputs/baseline/eval-run-1-ciprofloxacin-tendon_rupture_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:04:32 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-10-albuterol-suicidal_ideation_report.json`](outputs/baseline/eval-run-10-albuterol-suicidal_ideation_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:04:59 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-11-amoxicillin-tendon_rupture_report.json`](outputs/baseline/eval-run-11-amoxicillin-tendon_rupture_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:05:00 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-12-atorvastatin-common_cold_report.json`](outputs/baseline/eval-run-12-atorvastatin-common_cold_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:05:05 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-13-imatinib-tooth_eruption_report.json`](outputs/baseline/eval-run-13-imatinib-tooth_eruption_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:05:26 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-14-adalimumab-frostbite_report.json`](outputs/baseline/eval-run-14-adalimumab-frostbite_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:05:29 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-2-isotretinoin-teratogenicity_report.json`](outputs/baseline/eval-run-2-isotretinoin-teratogenicity_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:04:35 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-3-clozapine-agranulocytosis_report.json`](outputs/baseline/eval-run-3-clozapine-agranulocytosis_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:04:40 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-4-valproic_acid-hepatotoxicity_report.json`](outputs/baseline/eval-run-4-valproic_acid-hepatotoxicity_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:04:41 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-5-rosiglitazone-myocardial_infarction_report.json`](outputs/baseline/eval-run-5-rosiglitazone-myocardial_infarction_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:04:44 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-6-pembrolizumab-pneumonitis_report.json`](outputs/baseline/eval-run-6-pembrolizumab-pneumonitis_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:04:46 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-7-liraglutide-pancreatic_cancer_report.json`](outputs/baseline/eval-run-7-liraglutide-pancreatic_cancer_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:04:48 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-8-metformin-hypoglycaemia_report.json`](outputs/baseline/eval-run-8-metformin-hypoglycaemia_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:04:54 | `v1.0` | — | Frozen execution report |
| [`outputs/baseline/eval-run-9-atorvastatin-dementia_report.json`](outputs/baseline/eval-run-9-atorvastatin-dementia_report.json) | `baseline_report` | **PARTIAL** | — | 2026-08-14T12:04:56 | `v1.0` | — | Frozen execution report |
| [`outputs/confounding_probe/confounding_self_probe.json`](outputs/confounding_probe/confounding_self_probe.json) | `confounding_self_probe` | **MINIMAL** | — | — | — | — | Legacy diagnostic probe with raw metrics; missing all core provenance fields. |
| [`outputs/confounding_probe/metformin_confounding_report.json`](outputs/confounding_probe/metformin_confounding_report.json) | `confounding_probe_report` | **PARTIAL** | — | 2026-08-27T05:09:44 | `v1.1` | — | Frozen execution report |
| [`outputs/critic_probe/leakage_critique_results.json`](outputs/critic_probe/leakage_critique_results.json) | `critic_probe_results` | **MINIMAL** | — | — | — | — | Legacy diagnostic probe with raw metrics; missing all core provenance fields. |
| [`outputs/eval-run-0-montelukast-suicidal_ideation_report.json`](outputs/eval-run-0-montelukast-suicidal_ideation_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:23 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-1-ciprofloxacin-tendon_rupture_report.json`](outputs/eval-run-1-ciprofloxacin-tendon_rupture_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:24 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-10-albuterol-suicidal_ideation_report.json`](outputs/eval-run-10-albuterol-suicidal_ideation_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:35 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-11-amoxicillin-tendon_rupture_report.json`](outputs/eval-run-11-amoxicillin-tendon_rupture_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:36 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-12-atorvastatin-common_cold_report.json`](outputs/eval-run-12-atorvastatin-common_cold_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:37 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-13-imatinib-tooth_eruption_report.json`](outputs/eval-run-13-imatinib-tooth_eruption_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:38 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-14-adalimumab-frostbite_report.json`](outputs/eval-run-14-adalimumab-frostbite_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:39 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-2-isotretinoin-teratogenicity_report.json`](outputs/eval-run-2-isotretinoin-teratogenicity_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:25 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-3-clozapine-agranulocytosis_report.json`](outputs/eval-run-3-clozapine-agranulocytosis_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:26 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-4-valproic_acid-hepatotoxicity_report.json`](outputs/eval-run-4-valproic_acid-hepatotoxicity_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:28 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-5-rosiglitazone-myocardial_infarction_report.json`](outputs/eval-run-5-rosiglitazone-myocardial_infarction_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:29 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-6-pembrolizumab-pneumonitis_report.json`](outputs/eval-run-6-pembrolizumab-pneumonitis_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:30 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-7-liraglutide-pancreatic_cancer_report.json`](outputs/eval-run-7-liraglutide-pancreatic_cancer_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:32 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-8-metformin-hypoglycaemia_report.json`](outputs/eval-run-8-metformin-hypoglycaemia_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:33 | `v1.0` | — | Frozen execution report |
| [`outputs/eval-run-9-atorvastatin-dementia_report.json`](outputs/eval-run-9-atorvastatin-dementia_report.json) | `production_report` | **PARTIAL** | — | 2026-08-14T11:37:34 | `v1.0` | — | Frozen execution report |
| [`outputs/probe/probe-run-0-topiramate-hypohidrosis_report.json`](outputs/probe/probe-run-0-topiramate-hypohidrosis_report.json) | `diagnostic_probe_report` | **PARTIAL** | — | 2026-08-14T03:45:54 | `v1.0` | — | Frozen execution report |
| [`outputs/probe/probe-run-1-tamsulosin-intraoperative_floppy_iris_syndrome_report.json`](outputs/probe/probe-run-1-tamsulosin-intraoperative_floppy_iris_syndrome_report.json) | `diagnostic_probe_report` | **PARTIAL** | — | 2026-08-14T03:45:54 | `v1.0` | — | Frozen execution report |
| [`outputs/probe/probe-run-2-terbinafine-ageusia_report.json`](outputs/probe/probe-run-2-terbinafine-ageusia_report.json) | `diagnostic_probe_report` | **PARTIAL** | — | 2026-08-14T03:45:55 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-0-montelukast-suicidal_ideation_report.json`](outputs/react_agent/eval-run-0-montelukast-suicidal_ideation_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:40:55 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-1-ciprofloxacin-tendon_rupture_report.json`](outputs/react_agent/eval-run-1-ciprofloxacin-tendon_rupture_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:41:35 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-10-albuterol-suicidal_ideation_report.json`](outputs/react_agent/eval-run-10-albuterol-suicidal_ideation_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:47:27 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-11-amoxicillin-tendon_rupture_report.json`](outputs/react_agent/eval-run-11-amoxicillin-tendon_rupture_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:48:22 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-12-atorvastatin-common_cold_report.json`](outputs/react_agent/eval-run-12-atorvastatin-common_cold_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:48:42 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-13-imatinib-tooth_eruption_report.json`](outputs/react_agent/eval-run-13-imatinib-tooth_eruption_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:49:15 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-14-adalimumab-frostbite_report.json`](outputs/react_agent/eval-run-14-adalimumab-frostbite_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:50:07 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-2-isotretinoin-teratogenicity_report.json`](outputs/react_agent/eval-run-2-isotretinoin-teratogenicity_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:42:02 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-3-clozapine-agranulocytosis_report.json`](outputs/react_agent/eval-run-3-clozapine-agranulocytosis_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:42:42 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-4-valproic_acid-hepatotoxicity_report.json`](outputs/react_agent/eval-run-4-valproic_acid-hepatotoxicity_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:43:24 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-5-rosiglitazone-myocardial_infarction_report.json`](outputs/react_agent/eval-run-5-rosiglitazone-myocardial_infarction_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:44:05 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-6-pembrolizumab-pneumonitis_report.json`](outputs/react_agent/eval-run-6-pembrolizumab-pneumonitis_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:44:40 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-7-liraglutide-pancreatic_cancer_report.json`](outputs/react_agent/eval-run-7-liraglutide-pancreatic_cancer_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:45:12 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-8-metformin-hypoglycaemia_report.json`](outputs/react_agent/eval-run-8-metformin-hypoglycaemia_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:46:07 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent/eval-run-9-atorvastatin-dementia_report.json`](outputs/react_agent/eval-run-9-atorvastatin-dementia_report.json) | `react_agent_report` | **PARTIAL** | — | 2026-08-21T03:46:51 | `v1.0` | — | Frozen execution report |
| [`outputs/react_agent_agreement_report.json`](outputs/react_agent_agreement_report.json) | `agent_agreement_audit` | **MINIMAL** | — | — | — | — | Legacy diagnostic probe with raw metrics; missing all core provenance fields. |
| [`outputs/research/error_taxonomy/taxonomy_results.json`](outputs/research/error_taxonomy/taxonomy_results.json) | `research_taxonomy_experiment` | **PARTIAL** | — | 2026-08-30T11:32:32 | — | — | Intermediate probe or summary report with partial timestamp/metadata. |
| [`outputs/research/reproducibility_manifest.json`](outputs/research/reproducibility_manifest.json) | `reproducibility_manifest` | **PARTIAL** | `22e5f04c` | 2026-08-30T11:37:37 | — | `v7` | Self-indexing metadata manifest consolidating provenance across all repository outputs. |
| [`outputs/research/source_ablation/ablation_results.json`](outputs/research/source_ablation/ablation_results.json) | `research_ablation_experiment` | **COMPLETE** | `24b634ac` | 2026-08-29T15:13:50 | `v1.1` | `v7` | Full provenance recorded: commit hash, model, prompts, cache schema, config snapshot. |
| [`outputs/research/source_ablation/counterfactual_margins.json`](outputs/research/source_ablation/counterfactual_margins.json) | `research_ablation_experiment` | **COMPLETE** | `24b634ac` | 2026-08-29T15:13:50 | `v1.1` | `v7` | Full provenance recorded: commit hash, model, prompts, cache schema, config snapshot. |
| [`outputs/research/source_ablation/threshold_sensitivity.json`](outputs/research/source_ablation/threshold_sensitivity.json) | `research_ablation_experiment` | **COMPLETE** | `24b634ac` | 2026-08-29T15:13:50 | `v1.1` | `v7` | Full provenance recorded: commit hash, model, prompts, cache schema, config snapshot. |
| [`outputs/research/stability/repeated_run_variance.json`](outputs/research/stability/repeated_run_variance.json) | `research_stability_experiment` | **COMPLETE** | `80439503` | 2026-08-29T14:57:02 | `v1.1` | `v7` | Full provenance recorded: commit hash, model, prompts, cache schema, config snapshot. |
| [`outputs/research/stability/repeated_run_variance_confounding.json`](outputs/research/stability/repeated_run_variance_confounding.json) | `research_stability_experiment` | **COMPLETE** | `64ecb1e9` | 2026-08-29T17:31:43 | `v1.1` | `v7` | Full provenance recorded: commit hash, model, prompts, cache schema, config snapshot. |
| [`outputs/stability/loo_analysis.json`](outputs/stability/loo_analysis.json) | `stability_analysis` | **MINIMAL** | — | — | — | — | Legacy diagnostic probe with raw metrics; missing all core provenance fields. |
