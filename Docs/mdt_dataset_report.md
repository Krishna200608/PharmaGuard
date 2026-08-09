# OncoSwarm: MDT Dataset Research Report
**Compiled for:** IIIT Allahabad | 7th Semester Research Project  
**Team:** Krishna Sikheriya, Naitik Jain, Lokesh Bawariya  
**Supervisor:** Dr. Nikhilanand Arya

---

> [!IMPORTANT]
> **Honest Assessment First:** No single public dataset contains a "formal MDT board recommendation" as a discrete, machine-readable field. Real-world MDT transcripts are protected clinical data. The strategy is to use complementary datasets that together provide: (a) rich patient clinical/histology/molecular data, and (b) a treatment plan or survival outcome as a proxy for the MDT decision. This is the standard approach in every published paper in this space.

---

## Tier 1 — Primary Candidates (Most Suitable)

---

### 1. 🥇 TCGA (The Cancer Genome Atlas) via GDC Data Portal
| Field | Details |
|---|---|
| **Source / Institution** | NCI / NIH |
| **Dataset Link** | [https://portal.gdc.cancer.gov/](https://portal.gdc.cancer.gov/) |
| **Cancer Types** | 33 cancer types (LUAD, BRCA, COAD, PRAD, GBM, OV, KIRC, etc.) |
| **No. of Patients** | ~11,000 across all studies |
| **Key Clinical Fields** | Age, sex, race, TNM stage, prior treatment, vital status, days-to-death, days-to-last-follow-up |
| **Histology Available?** | ✅ Yes — ICD-O-3 morphology codes (e.g., adenocarcinoma, squamous cell carcinoma); WSI slides via TCIA |
| **Molecular / Genomic Data?** | ✅ Yes — Mutations (MAF), CNV, RNA-seq, miRNA, methylation, protein (RPPA) |
| **Imaging?** | ✅ Pathology WSI + Radiology CT/MRI via linked TCIA collections |
| **Treatment Decision Available?** | ✅ Partial — Chemotherapy, radiation, surgery fields in clinical XML |
| **MDT Recommendation?** | ❌ No formal MDT transcript |
| **Clinical Outcome?** | ✅ Yes — OS, PFI, DFI, DSS survival endpoints |
| **Access Type** | Public (Open Access clinical + most genomic) / Controlled (raw reads via dbGaP) |
| **License** | NIH GDC Data Use Agreement |
| **Why Suitable** | The gold-standard multi-omic cancer dataset. Rich histology + molecular + treatment + survival data make it the backbone of any oncology ML project. Used as ground truth in virtually every published MDT-AI paper. |

---

### 2. 🥇 cBioPortal for Cancer Genomics
| Field | Details |
|---|---|
| **Source / Institution** | MSKCC / Dana-Farber / Broad Institute |
| **Dataset Link** | [https://www.cbioportal.org/](https://www.cbioportal.org/) |
| **Cancer Types** | 300+ curated studies (breast, lung, colorectal, prostate, glioma, etc.) |
| **No. of Patients** | 100,000+ across all studies |
| **Key Clinical Fields** | Age, sex, stage, histology subtype, ECOG status (study-dependent), prior therapy, DFS/OS |
| **Histology Available?** | ✅ Yes — Cancer subtype, morphology in curated clinical tabs |
| **Molecular / Genomic Data?** | ✅ Yes — Mutations, fusions, CNVs, expression, CNA, MSI, TMB |
| **Imaging?** | ❌ No native imaging (links to TCIA for select studies) |
| **Treatment Decision Available?** | ✅ Partial — Therapy lines in some studies (e.g., MSK-IMPACT clinical) |
| **MDT Recommendation?** | ❌ No |
| **Clinical Outcome?** | ✅ Yes — OS, DFS, PFS across most studies |
| **Access Type** | Public |
| **License** | Open (varies by study; most CC BY 4.0) |
| **Why Suitable** | The most user-friendly interface for multi-omic cancer data. The MSK-IMPACT studies (>80,000 patients) include real clinical treatment context alongside genomics. Excellent for RAG knowledge-base construction. |

---

### 3. 🥇 CPTAC (Clinical Proteomic Tumor Analysis Consortium)
| Field | Details |
|---|---|
| **Source / Institution** | NCI / NIH |
| **Dataset Link** | [https://pdc.cancer.gov/](https://pdc.cancer.gov/) |
| **Cancer Types** | Breast, lung, colon, ovarian, uterine, GBM, PDAC, HNSCC, LUSC, CCRCC |
| **No. of Patients** | ~1,500 across studies |
| **Key Clinical Fields** | Age, sex, BMI, race, tumor stage, histology, prior surgery |
| **Histology Available?** | ✅ Yes — Detailed pathology reports in metadata |
| **Molecular / Genomic Data?** | ✅ Yes — Proteomics, phosphoproteomics, metabolomics + genomics |
| **Imaging?** | ✅ Pathology WSI + Radiology via TCIA (CPTAC-3 collection) |
| **Treatment Decision Available?** | ✅ Partial — Chemotherapy, surgical resection status |
| **MDT Recommendation?** | ❌ No |
| **Clinical Outcome?** | ✅ Yes — OS, recurrence, pathological response |
| **Access Type** | Public |
| **License** | NIH CPTAC Data Use Agreement |
| **Why Suitable** | Uniquely adds proteomics/phosphoproteomics — a layer no other public dataset has. Excellent for cases where molecular biomarker reasoning is the focus (e.g., why HER2+ → trastuzumab). |

---

### 4. 🥇 SEER (Surveillance, Epidemiology, and End Results)
| Field | Details |
|---|---|
| **Source / Institution** | NCI / NIH |
| **Dataset Link** | [https://seer.cancer.gov/data/](https://seer.cancer.gov/data/) |
| **Cancer Types** | All major cancers (US population-based registry) |
| **No. of Patients** | 10+ million patients (largest cancer dataset in the world) |
| **Key Clinical Fields** | Age, sex, race, county, histology code, primary site, stage, first-course treatment (surgery, radiation, chemo flag), survival |
| **Histology Available?** | ✅ Yes — ICD-O-3 histology/morphology codes; detailed and standardized |
| **Molecular / Genomic Data?** | ⚠️ Limited — ER/PR/HER2 for breast; PSA for prostate; MSI status in newer releases |
| **Imaging?** | ❌ No |
| **Treatment Decision Available?** | ✅ Yes — Surgery, radiation, chemotherapy (binary/flag fields) |
| **MDT Recommendation?** | ❌ No |
| **Clinical Outcome?** | ✅ Yes — Cause-specific survival, overall survival |
| **Access Type** | Registration Required (free SEER*Stat account) |
| **License** | NCI SEER Data Use Agreement |
| **Why Suitable** | The sheer scale (10M+ patients) makes it unmatched for population-level treatment pattern analysis. Excellent for training a model on "which cancer type + stage → which first-line treatment" mappings. |

---

## Tier 2 — Strong Supporting Datasets

---

### 5. TCIA (The Cancer Imaging Archive) — TCGA Linked Collections
| Field | Details |
|---|---|
| **Source / Institution** | NCI |
| **Dataset Link** | [https://www.cancerimagingarchive.net/](https://www.cancerimagingarchive.net/) |
| **Cancer Types** | 30+ (linked TCGA-LUAD, TCGA-BRCA, CPTAC-3, etc.) |
| **No. of Patients** | Varies by collection; up to 1,000+ per project |
| **Histology Available?** | ✅ Yes — Digital pathology WSI slides |
| **Molecular / Genomic Data?** | ✅ Via TCGA case IDs (linkable) |
| **Imaging?** | ✅ CT, MRI, PET, Pathology WSI |
| **Treatment Decision Available?** | ✅ Via linked TCGA clinical metadata |
| **MDT Recommendation?** | ❌ No |
| **Clinical Outcome?** | ✅ Via linked TCGA |
| **Access Type** | Public |
| **License** | CC BY 3.0 / TCIA Restricted License (varies) |
| **Why Suitable** | The critical bridge for multi-modal data. TCIA provides the raw imaging (CT, WSI) that links back to TCGA's clinical/genomic data via shared patient IDs. Essential for Radiologist Agent and Pathologist Agent RAG grounding. |

---

### 6. MSK-IMPACT Clinical Sequencing (via cBioPortal)
| Field | Details |
|---|---|
| **Source / Institution** | Memorial Sloan Kettering |
| **Dataset Link** | [https://www.cbioportal.org/study/summary?id=msk_impact_2017](https://www.cbioportal.org/study/summary?id=msk_impact_2017) |
| **Cancer Types** | Pan-cancer (all solid tumors) |
| **No. of Patients** | 10,945 (2017 study); updated cohorts >80,000 |
| **Key Clinical Fields** | Cancer type, histology, primary site, metastatic status, treatment lines, OS |
| **Histology Available?** | ✅ Yes |
| **Molecular / Genomic Data?** | ✅ Yes — 341/468-gene panel (EGFR, KRAS, BRCA, ALK, HER2, etc.) |
| **Imaging?** | ❌ No |
| **Treatment Decision Available?** | ✅ Partial — Lines of therapy recorded |
| **MDT Recommendation?** | ❌ No |
| **Clinical Outcome?** | ✅ Yes |
| **Access Type** | Public |
| **License** | CC BY-NC 4.0 |
| **Why Suitable** | Real-world clinical sequencing data from a top cancer institution. Ideal for training the Oncologist Agent's reasoning on "mutation X in cancer Y → targeted therapy Z". |

---

### 7. MIMIC-IV Oncology Notes (via PhysioNet)
| Field | Details |
|---|---|
| **Source / Institution** | MIT / Beth Israel Deaconess Medical Center |
| **Dataset Link** | [https://physionet.org/content/mimiciv/](https://physionet.org/content/mimiciv/) |
| **Cancer Types** | All (unstructured; extracted via NLP from ICU notes) |
| **No. of Patients** | 300,000+ hospital admissions |
| **Key Clinical Fields** | Labs (CBC, LFT, KFT), medications, diagnoses (ICD codes), free-text clinical notes |
| **Histology Available?** | ⚠️ Partial — Embedded in pathology notes (NLP extraction needed) |
| **Molecular / Genomic Data?** | ❌ No |
| **Imaging?** | ⚠️ Radiology reports (text only, no images) |
| **Treatment Decision Available?** | ✅ Yes — Medications, procedures, clinical decisions in notes |
| **MDT Recommendation?** | ⚠️ Possible — Oncology consult notes may contain MDT discussions (requires NLP mining) |
| **Clinical Outcome?** | ✅ Yes — In-hospital mortality, readmission, LOS |
| **Access Type** | Credentialed (free, requires PhysioNet account + CITI training) |
| **License** | PhysioNet Credentialed Health Data License |
| **Why Suitable** | Uniquely provides *real clinical note text* — the kind of free-form reasoning that an MDT board would produce. Mining oncology consult notes from MIMIC-IV is an advanced but powerful technique for the Consensus Module training. |

---

## Tier 3 — Supplementary & Specialized

---

### 8. Kaggle — MSK "Personalized Medicine: Redefining Cancer Treatment"
| Field | Details |
|---|---|
| **Source / Institution** | MSKCC / Kaggle |
| **Dataset Link** | [https://www.kaggle.com/c/msk-redefining-cancer-treatment/data](https://www.kaggle.com/c/msk-redefining-cancer-treatment/data) |
| **Cancer Types** | Pan-cancer (mutation-focused) |
| **No. of Patients** | 3,321 annotated variants |
| **Key Clinical Fields** | Gene, mutation/variant, clinical evidence text |
| **Histology Available?** | ❌ No |
| **Molecular / Genomic Data?** | ✅ Yes — Gene + variant + class (1–9 oncogenic/benign) |
| **Imaging?** | ❌ No |
| **Treatment Decision Available?** | ⚠️ Implied (each class → treatment relevance) |
| **MDT Recommendation?** | ❌ No |
| **Clinical Outcome?** | ❌ No |
| **Access Type** | Public (Kaggle account) |
| **License** | Competition rules |
| **Why Suitable** | A clean, labeled dataset specifically designed for mutation → clinical decision classification. Ideal for training/testing the Oncologist Agent's genomic reasoning sub-module. |

---

### 9. PMC-Patients (PubMed Central Patient Summaries)
| Field | Details |
|---|---|
| **Source / Institution** | NIH / PubMed Central |
| **Dataset Link** | [https://huggingface.co/datasets/zhengyun21/PMC-Patients](https://huggingface.co/datasets/zhengyun21/PMC-Patients) |
| **Cancer Types** | All (case reports from medical literature) |
| **No. of Patients** | 167,000 patient summaries |
| **Key Clinical Fields** | Patient demographics, clinical history, diagnosis, treatment, outcomes (from case reports) |
| **Histology Available?** | ✅ Partial (embedded in case text) |
| **Molecular / Genomic Data?** | ✅ Partial |
| **Imaging?** | ❌ No |
| **Treatment Decision Available?** | ✅ Yes — Case reports explicitly describe final treatment |
| **MDT Recommendation?** | ⚠️ Partial — Some case reports describe MDT discussions |
| **Clinical Outcome?** | ✅ Yes |
| **Access Type** | Public (HuggingFace) |
| **License** | CC BY 4.0 |
| **Why Suitable** | The closest thing to a "ground truth treatment decision" dataset available publicly. Each case report is a complete story: patient → diagnosis → specialist reasoning → treatment → outcome. Directly models the MDT narrative. |

---

### 10. OncoTrialLLM — Genomic Biomarkers from Clinical Trials
| Field | Details |
|---|---|
| **Source / Institution** | BIMSB Bioinfo Lab (Research GitHub) |
| **Dataset Link** | [https://github.com/BIMSBbioinfo/oncotrialLLM](https://github.com/BIMSBbioinfo/oncotrialLLM) |
| **Cancer Types** | Pan-cancer (clinical trial data) |
| **No. of Patients** | Thousands of annotated trial records |
| **Key Clinical Fields** | Genomic biomarkers, eligibility criteria, trial intervention (drug/therapy) |
| **Histology Available?** | ✅ Partial |
| **Molecular / Genomic Data?** | ✅ Yes — Biomarker extraction from trial text |
| **Imaging?** | ❌ No |
| **Treatment Decision Available?** | ✅ Yes — Trial arm = treatment recommendation |
| **MDT Recommendation?** | ❌ No |
| **Clinical Outcome?** | ⚠️ Partial |
| **Access Type** | Public (GitHub) |
| **License** | MIT |
| **Why Suitable** | Provides a labeled "biomarker → treatment" mapping sourced from real clinical trials. Useful for grounding the Oncologist Agent's trial-matching capability. |

---

## Final Ranking Summary

| Rank | Dataset | MDT Score | Rationale |
|------|---------|-----------|-----------|
| 🥇 1 | **TCGA (via GDC)** | ★★★★★ | Most complete: histology + molecular + treatment + survival. The backbone. |
| 🥇 2 | **cBioPortal (MSK-IMPACT)** | ★★★★★ | Real-world genomics + clinical context, easiest API access. |
| 🥇 3 | **CPTAC** | ★★★★☆ | Unique proteomics layer; linked to imaging via TCIA. |
| 🥈 4 | **SEER** | ★★★★☆ | Massive scale; excellent histology + treatment flags. |
| 🥈 5 | **PMC-Patients** | ★★★★☆ | Closest to MDT narrative; 167K real case reports with treatment decisions. |
| 🥉 6 | **TCIA** | ★★★☆☆ | Essential imaging companion; must be linked with TCGA/CPTAC. |
| 🥉 7 | **MSK "Personalized Medicine" (Kaggle)** | ★★★☆☆ | Labeled mutation classification; no demographics. |
| 4 | **MIMIC-IV** | ★★★☆☆ | Free-text treatment decisions in notes (NLP needed). |
| 5 | **OncoTrialLLM** | ★★☆☆☆ | Biomarker-to-trial mapping; supplementary only. |

---

## Recommended Integration Strategy for OncoSwarm

Since no single dataset has all required fields, we recommend a **3-layer complementary approach**:

```
Layer 1 (BACKBONE)    → TCGA + cBioPortal (MSK-IMPACT)
                         Rich patient + histology + genomics + treatment + survival
                         
Layer 2 (NARRATIVE)   → PMC-Patients
                         Provides the "reasoning chain" (case report text → treatment)
                         Used for fine-tuning or few-shot examples for the agents
                         
Layer 3 (IMAGING RAG) → TCIA + CPTAC
                         Provides WSI pathology slides and CT/MRI linked to TCGA patients
                         Used to ground the Pathologist and Radiologist agents
```

**Linking Key:** All three layers share TCGA Patient IDs (e.g., `TCGA-AB-1234`), allowing them to be joined at the patient level without any additional work.

---

> [!TIP]
> **For your Colab Prototype:** Start with TCGA-LUAD (lung adenocarcinoma, ~560 patients) or TCGA-BRCA (breast cancer, ~1,084 patients) as these are the most thoroughly documented and have the best coverage of histology, molecular, and treatment fields. Use the `TCGAbiolinks` R package or the `gdc-client` Python tool to download clinical TSVs directly.
