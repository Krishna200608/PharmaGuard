# PharmaGuard — Live Triage Test Cases & Validation Guide

**Document Target:** `docs/test_cases.md`  
**Purpose:** Standardized test suites for validating the **PharmaGuard Live Signal Triage Dashboard** across NLP canonicalization, fuzzy spelling auto-correction, brand/lay-term alias mapping, and tri-stream regulatory gating.  
**System Architecture:** Two-Stage Term Canonicalization Layer (`pharmaguard/utils/canonicalize.py` per `CANONICALIZATION.md`) + FixedPipeline Multi-Stream Orchestrator (`FixedPipelineAgent`).

---

## 1. Quick Testing Instructions

1. **Launch the Application:**
   ```bash
   python run.py
   ```
   *Terminal 1 boots the local Ollama inference server (`qwen2.5:7b`). Terminal 2 boots the Streamlit clinical dashboard at `http://localhost:8501`.*

2. **Navigate to Live Signal Triage:**
   - In the sidebar or top tab bar, select **Live Signal Triage**.
   - Ensure the backend is set to **Ollama — qwen2.5:7b (Local / Unmetered)** or **Gemini 3.1 Flash**.

3. **Input Fields:**
   - Type the test values into the **Drug Name** and **Adverse Event** text input boxes.
   - Observe the real-time **NLP Pill** appearing beneath the input boxes before clicking.
   - Click **Run Triage** to execute the live multi-stream pipeline.

---

## 2. Test Suite 1: Ambiguity & "Did You Mean...?" Suggestion Flags ($0.65 \le S < 0.85$)

These test cases feature truncated stems, root prefixes, or related clinical phenotypes that land in the **$0.65 \le S < 0.85$ Ambiguity Band**. Rather than making an ungrounded clinical assumption, PharmaGuard prompts the user with an interactive suggestion badge.

| Test Case ID | Drug Name Input | Adverse Event Input | Real-Time NLP UI Banner | What the Engine Does | Expected Triage Verdict |
|:---:|---|---|---|---|:---:|
| **SUITE1-01** | `lisinopril` | `kidney injury` | `Did you mean: acute kidney injury for 'kidney injury'? (81% match)` | Flags for review; queries as entered if unedited | **`ESCALATE`** (Confidence: 1.0000, 9.4k FAERS reports) |
| **SUITE1-02** | `ciproflox` | `tendon rupture` | `Did you mean: ciprofloxacin for 'ciproflox'? (82% match)` | Flags truncated drug stem; prompts generic INN | **`ESCALATE`** (Boxed warning Achilles rupture) |
| **SUITE1-03** | `atorva` | `pneumonia` | `Did you mean: atorvastatin for 'atorva'? (67% match)` &middot; `Did you mean: pneumonitis for 'pneumonia'? (80% match)` | Prompts on both truncated drug and distinct lung phenotype | **`DO_NOT_ESCALATE`** (Negative control) |
| **SUITE1-04** | `sertral` | `pancreas` | `Did you mean: sertraline for 'sertral'? (82% match)` &middot; `Did you mean: pancreatitis for 'pancreas'? (80% match)` | Prompts drug generic and organ-to-event expansion | **`MONITOR`** / **`DO_NOT_ESCALATE`** |
| **SUITE1-05** | `clindamy` | `frost` | `Did you mean: clindamycin for 'clindamy'? (84% match)` &middot; `Did you mean: frostbite for 'frost'? (71% match)` | Identifies high-overlap prefix for drug and adverse event | **`DO_NOT_ESCALATE`** (Negative control) |
| **SUITE1-06** | `amoxici` | `agranulo` | `Did you mean: amoxicillin for 'amoxici'? (78% match)` &middot; `Did you mean: agranulocytosis for 'agranulo'? (70% match)` | Prompts on both truncated stems | **`MONITOR`** (Low-count spontaneous signal) |

---

## 3. Test Suite 2: High-Confidence Fuzzy Spelling Auto-Correction ($S \ge 0.85$)

These test cases test typographical errors, missing characters, phonetic substitutions, and trailing letters. PharmaGuard computes a SequenceMatcher score $S \ge 0.85$ and **automatically resolves the term to its canonical target** without blocking or failing the query.

| Test Case ID | Drug Name (Typed with Typo) | Adverse Event (Typed with Typo) | NLP Auto-Correct Resolution | Similarity Scores | Expected Triage Verdict |
|:---:|---|---|---|---|:---:|
| **SUITE2-01** | `lisinoprll` | `angioedma` | `lisinopril` $\longleftrightarrow$ `angioedema` | Drug: 90.0%, Event: 94.7% | **`ESCALATE`** (ACE inhibitor Black Box warning) |
| **SUITE2-02** | `montelucast` | `suicidal ideations` | `montelukast` $\longleftrightarrow$ `suicidal_ideation` | Drug: 90.9%, Event: 96.0% | **`MONITOR`** (Neuropsychiatric caution, Low MoA) |
| **SUITE2-03** | `ciprofloxacine` | `tendon tear` | `ciprofloxacin` $\longleftrightarrow$ `tendon_rupture` | Drug: 96.3%, Event: 98.0% | **`ESCALATE`** (Confirmed fluoroquinolone Boxed Warning) |
| **SUITE2-04** | `atorvastat` | `rhabdomyolisis` | `atorvastatin` $\longleftrightarrow$ `rhabdomyolysis` | Drug: 90.9%, Event: 92.9% | **`ESCALATE`** (Statin myopathy / rhabdomyolysis signal) |
| **SUITE2-05** | `citalopramm` | `couugh` | `citalopram` $\longleftrightarrow$ `cough` | Drug: 95.2%, Event: 90.9% | **`DO_NOT_ESCALATE`** (Benign negative control) |
| **SUITE2-06** | `valproic acid` | `hepatoxicity` | `valproic_acid` $\longleftrightarrow$ `hepatotoxicity` | Drug: 100.0%, Event: 92.3% | **`ESCALATE`** (Fatal hepatotoxicity Boxed Warning) |
| **SUITE2-07** | `metform` | `lactic acidosis` | `metformin` $\longleftrightarrow$ `lactic_acidosis` | Drug: 87.5%, Event: 98.0% | **`ESCALATE`** (MALA mitochondrial complex I signal) |

---

## 4. Test Suite 3: Commercial Brand Names & Lay-Term Synonyms ($S = 0.98$)

Frontline patients, clinicians, and electronic health records frequently record commercial trade names or colloquial lay expressions. PharmaGuard's deterministic Stage 1B alias table translates these into generic INN active substances and MedDRA Preferred Terms (PTs).

| Test Case ID | Commercial Brand Name | Lay / Colloquial Reaction | Canonical Medical Translation | Pharmacovigilance Mechanism & Grounding | Expected Verdict |
|:---:|---|---|---|---|:---:|
| **SUITE3-01** | `zestril` | `swelling of lips` | `lisinopril` $\longleftrightarrow$ `angioedema` | Kininase II inhibition $\to$ bradykinin accumulation | **`ESCALATE`** |
| **SUITE3-02** | `singulair` | `suicidality` | `montelukast` $\longleftrightarrow$ `suicidal_ideation` | CysLT1 antagonism; high postmarketing surveillance | **`MONITOR`** |
| **SUITE3-03** | `lipitor` | `muscle breakdown` | `atorvastatin` $\longleftrightarrow$ `rhabdomyolysis` | HMG-CoA reductase inhibition $\to$ myocyte necrosis | **`ESCALATE`** |
| **SUITE3-04** | `avandia` | `heart attack` | `rosiglitazone` $\longleftrightarrow$ `myocardial_infarction` | PPAR-gamma agonism and fluid retention | **`ESCALATE`** |
| **SUITE3-05** | `glucophage` | `mala` | `metformin` $\longleftrightarrow$ `lactic_acidosis` | Biguanide-induced hepatic lactate accumulation | **`ESCALATE`** |
| **SUITE3-06** | `prozac` | `gi bleed` | `fluoxetine` $\longleftrightarrow$ `gastrointestinal_haemorrhage` | SSRI platelet serotonin reuptake depletion | **`ESCALATE`** |
| **SUITE3-07** | `cozaar` | `laryngeal edema` | `losartan` $\longleftrightarrow$ `angioedema` | AT1 receptor blocker cross-reactivity warning | **`ESCALATE`** |
| **SUITE3-08** | `lasix` | `kidney failure` | `furosemide` $\longleftrightarrow$ `acute_kidney_injury` | Loop diuretic prerenal azotemia / volume depletion | **`ESCALATE`** |
| **SUITE3-09** | `ozempic` | `acute pancreatitis` | `semaglutide` $\longleftrightarrow$ `pancreatitis` | GLP-1 receptor hyperstimulation of pancreatic duct | **`ESCALATE`** |
| **SUITE3-10** | `keytruda` | `lung inflammation` | `pembrolizumab` $\longleftrightarrow$ `pneumonitis` | PD-1 blockade immune-mediated toxicities | **`ESCALATE`** |

---

## 5. Test Suite 4: US vs. UK Orthographic / MedDRA PT Dialect Divergences

Spontaneous reporting databases (such as FAERS) index adverse reactions under **British English MedDRA PTs**. Querying FAERS with American English variants can silently return zero reports (`DECISIONS.md §21`). PharmaGuard's alias engine seamlessly reconciles these spelling conventions.

| Test Case ID | Drug Name | US English Input | Reconciled MedDRA PT (UK) | FAERS Impact if Unmapped | Expected Verdict |
|:---:|---|---|---|---|:---:|
| **SUITE4-01** | `metformin` | `hypoglycemia` | `hypoglycaemia` | Reconciles 0 reports (US) $\to$ 9,344 reports (UK) | **`DO_NOT_ESCALATE`** (Monotherapy negative control) |
| **SUITE4-02** | `aspirin` | `gastrointestinal hemorrhage` | `gastrointestinal_haemorrhage` | Reconciles 0 reports (US) $\to$ 14,210 reports (UK) | **`ESCALATE`** (Severe COX-1 mucosal bleeding) |
| **SUITE4-03** | `lisinopril` | `angioneurotic oedema` | `angioedema` | Maps obsolete British synonym to current PT | **`ESCALATE`** (Priority 1 Action) |
| **SUITE4-04** | `losartan` | `hyperkalemia` | `hyperkalaemia` | Reconciles US `hyperkalemia` to MedDRA `hyperkalaemia` | **`ESCALATE`** (Aldosterone attenuation) |

---

## 6. Test Suite 5: Regulatory Gating & Decision Boundary Benchmarks

These test cases validate PharmaGuard's **epistemic safety gates**, demonstrating why tool-grounded triage outperforms ungrounded single-shot LLMs.

| Scenario Archetype | Candidate Pair | Why PharmaGuard Triages Correctly | Triage Decision | Gating Rule Exercised |
|---|---|---|:---:|---|
| **Confirmed Regulatory Hazard** | `ciprofloxacin` $\longleftrightarrow$ `tendon rupture` | All 3 streams corroborate: FAERS PRR=8.45, PubMed Grade A, ChEMBL Moderate. | **`ESCALATE`** | Composite Confidence $\ge 0.70$ + Strong Signal |
| **Mechanistic Uncertainty** | `montelukast` $\longleftrightarrow$ `suicidal ideation` | Strong FAERS ($N=3,540$) and Grade A literature, but Low receptor plausibility (no central CysLT1 pathway). Confidence correctly dampened to 0.664. | **`MONITOR`** | Lenient TP ($[0.35, 0.70)$ active surveillance band) |
| **Hard Safety Gate 1 Override** | `metformin` $\longleftrightarrow$ `common cold` | Real-world FAERS reports are zero/noise ($PRR < 1.5$). Hard Gate 1 immediately suppresses false alarm regardless of LLM confidence. | **`DO_NOT_ESCALATE`** | `FAERS == NO_SIGNAL` forces `DO_NOT_ESCALATE` |
| **Refuted Historical Controversy** | `liraglutide` $\longleftrightarrow$ `pancreatic cancer` | Ungrounded LLMs hallucinate escalation on historical rumors. PharmaGuard grounds against post-2014 FDA/EMA safety review: FAERS NO_SIGNAL. | **`DO_NOT_ESCALATE`** | Hard Gate 1 suppresses refuted signal (`DECISIONS.md §13`) |
| **Benign Class Effect** | `lisinopril` $\longleftrightarrow$ `cough` | Spontaneous reports reflect frequent class effect (bradykinin bronchial accumulation), but benign nature does not warrant high-priority alert. | **`DO_NOT_ESCALATE`** | Gating suppresses non-critical alert fatigue |

---

## 7. Test Suite 6: Open Query Novel Inputs ($S < 0.65$)

These test cases verify that typing a drug or adverse event outside the 50-drug canonical vocabulary does **not** crash the dashboard or get blocked. The system preserves the raw input and queries live external APIs.

| Test Case ID | Drug Name (Open Term) | Adverse Event (Open Term) | System Behavior |
|:---:|---|---|---|
| **SUITE6-01** | `paracetamol` | `headache` | Retains raw input; queries openFDA and PubMed directly. |
| **SUITE6-02** | `gabapentin` | `somnolence` | Resolves `gabapentin` in ChEMBL; queries FAERS live. |
| **SUITE6-03** | `amoxicillin` | `anaphylaxis` | Executes live immunologic acute hypersensitivity screening. |

---

## 8. Verification Matrix & Checklist

Use this checklist when executing validation runs for research presentations, capstone defense demos, or conference exhibits:

- [ ] **Real-Time NLP Feedback:** Input pill displays correct match type (`Auto-Correct`, `Alias`, or `Suggestion`).
- [ ] **Zero Unicode Emojis:** Clinical dossier renders with clean, formal brackets (`[ESCALATE]`, `[MONITOR]`, `[DO_NOT_ESCALATE]`).
- [ ] **Evans Criteria Audit:** FAERS table displays `PRR >= 2.0`, $N \ge 3$, and Lower CI $> 1.0$ status.
- [ ] **KaTeX Mathematical Integrity:** Confidence formula renders cleanly without raw backslashes.
- [ ] **Audit Provenance:** SHA-256 integrity hash is populated on the generated briefing document.
- [ ] **Unit Test Regression:** All 245 test suite assertions pass (`pytest`).
