# Project Proposal: OncoSwarm - Multi-Agent Virtual Tumor Board

**Institution:** Indian Institute of Information Technology (IIIT), Allahabad  
**Course:** B.Tech Information Technology | 7th Semester (2026-27)  
**Supervisor:** Dr. Nikhilanand Arya  

**Project Team:**  
- Krishna Sikheriya (IIT2023139)
- Naitik Jain (IIB2023036)  
- Lokesh Bawariya (IIT2023138)  

---

## 1. Introduction and Problem Statement
In precision oncology, treatment decisions for complex cancer cases require a "Tumor Board"—a multidisciplinary panel of specialists (e.g., pathologists, radiologists, oncologists). However, convening such boards is time-consuming, expensive, and unavailable in resource-constrained clinical settings. 

While Large Language Models (LLMs) show promise in medical QA, a single LLM operating in isolation suffers from "hallucinations" and lacks the specialized, multi-perspective reasoning required for high-stakes oncology decisions. 

## 2. Proposed Solution: OncoSwarm
We propose **OncoSwarm**, a Multi-Agent System (MAS) where specialized LLM agents collaborate to simulate a Virtual Tumor Board. Each agent acts as a specific medical specialist with its own prompt persona and knowledge base (via Retrieval-Augmented Generation). The agents debate a patient's case, cross-check each other for factual inaccuracies, and use a consensus mechanism to arrive at a final treatment recommendation.

## 3. Base Paper Selection and Literature Review
We have reviewed the following 5 state-of-the-art papers in agentic healthcare AI:

1. **[BASE PAPER] MDAT: Multidisciplinary Large Language Model Agent Teams for Precision Oncology Enhance Complex Gynecologic Oncology Decision Support**  
   *Link:* [https://www.medrxiv.org/content/10.1101/2025.10.30.25339199v1](https://www.medrxiv.org/content/10.1101/2025.10.30.25339199v1)  
   *Why it's chosen:* This paper directly proposes simulating a multidisciplinary team via deliberation, voting, and consensus building to resolve clinical discordance. It perfectly aligns with the OncoSwarm vision.
2. **Demo: Healthcare Agent Orchestrator (HAO) for Patient Summarization in Molecular Tumor Boards**  
   *Link:* [https://arxiv.org/abs/2509.06602](https://arxiv.org/abs/2509.06602)  
   *Focus:* Multi-agent coordination for patient record summarization.
3. **PRISM: Patient Records Interpretation for Semantic Clinical Trial Matching using Large Language Models**  
   *Link:* [https://arxiv.org/abs/2404.15549](https://arxiv.org/abs/2404.15549)  
   *Focus:* Agentic frameworks for matching patient records to clinical trial criteria.
4. **MedAgentBench: A Realistic Virtual EHR Environment to Benchmark Medical LLM Agents**  
   *Link:* [https://arxiv.org/abs/2501.14654](https://arxiv.org/abs/2501.14654)  
   *Focus:* Open-source benchmarks and FHIR-based evaluation of medical agents.
5. **Improving Factuality and Reasoning in Language Models through Multiagent Debate**  
   *Link:* [https://arxiv.org/abs/2305.14325](https://arxiv.org/abs/2305.14325)  
   *Focus:* Foundational paper proving that debate and cross-examination reduce LLM hallucinations.

**Selected Base Paper:** We will use **MDAT** as our foundational architecture, extending its voting mechanism with our own RAG-powered specific specialist roles and evaluating it on open-source medical datasets.

## 4. System Architecture
The system will be orchestrated using **LangGraph** or **CrewAI**, enabling cyclic or sequential workflows:
- **Orchestrator Agent:** Receives the patient vignette and delegates analysis.
- **Pathologist Agent:** Analyzes biopsy reports; RAG over pathology textbooks.
- **Radiologist Agent:** Interprets imaging text; RAG over radiology guidelines.
- **Medical Oncologist Agent:** Recommends systemic therapy; RAG over NCCN protocols.
- **Consensus Module (The "Board"):** A specialized function that forces the agents into a multi-round debate if their initial treatment proposals differ. It outputs a final confidence score and treatment plan.

## 5. Datasets and Resources
- **Data Sources:** 
  - **MedQA (USMLE) Dataset:** [https://huggingface.co/datasets/bigbio/med_qa](https://huggingface.co/datasets/bigbio/med_qa) (HuggingFace)
    * Github Link : [https://github.com/jind11/MedQA](https://github.com/jind11/MedQA)
  - **MedAgentBench:** [https://github.com/Stanford-Health/MedAgentBench](https://github.com/Stanford-Health/MedAgentBench) (GitHub)
  - **Synthetic Vignettes:** Custom LLM-generated structured clinical vignettes (to avoid HIPAA/IRB restrictions during rapid prototyping).
    * *Brief:* Since real patient records require lengthy ethics approvals and privacy compliance (HIPAA), we will use an LLM to generate highly realistic, hypothetical cancer patient cases. This bypasses legal roadblocks and allows us to rapidly generate complex cases to test the agents' debate capabilities.
- **Compute (Colab Feasibility):** 
  - We will use **Gemini 2.0 Flash API** (free tier) as the primary reasoning engine, which shifts the compute burden off local GPUs.
  - For local execution, we will fine-tune **Llama-3-8B** using QLoRA via Unsloth, which comfortably fits on Google Colab’s 16GB T4 / L4 GPUs.
- **Vector Database:** ChromaDB (in-memory) for RAG document retrieval.
  * *Brief:* To ensure our agents do not hallucinate, they will use Retrieval-Augmented Generation (RAG) to "read" official oncology guidelines before answering. ChromaDB converts these massive medical textbooks into mathematical vectors, allowing the agents to instantly search and retrieve the exact relevant clinical protocols. Running it "in-memory" means zero server setup or hosting costs, making it perfectly suited for execution on Google Colab.

## 6. Evaluation Metrics
Unlike classification tasks (where AUC is primary), this agentic system will be evaluated on:
1. **Consensus Accuracy:** Does the final plan match the ground-truth medical guideline?
2. **Hallucination Reduction Rate:** How many errors were caught during the debate phase compared to a single-shot LLM response?
3. **Agent Agreement/Discordance Score:** The statistical convergence of the agents over $N$ rounds.

## 7. Project Timeline (Tentative)
- **Phase 1 (Pre-Midsem):** Base paper replication (MDAT mechanics) and environment setup (CrewAI/LangGraph).
- **Phase 2 (Pre-Midsem):** Agent Persona design and RAG pipeline integration (ChromaDB + NCCN guidelines).
- **Midsem Evaluation:** Present working prototype of agents communicating and fetching basic RAG documents.
- **Phase 3 (Post-Midsem):** Implementation of the multi-round debate protocol and complex agent routing.
- **Phase 4 (Post-Midsem):** Rigorous evaluation on synthetic vignettes and MedQA datasets; running ablation studies (Single LLM vs. MAS).
- **Endsem Evaluation:** Finalize Streamlit Dashboard, compile evaluation metrics, write the research paper, and prepare for IEEE conference submission.
