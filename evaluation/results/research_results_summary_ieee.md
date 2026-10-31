# ClinGap-NLP: IEEE Conference Paper Results and Evaluation Section (Audited & Verified)

## IV. EXPERIMENTAL RESULTS AND EVALUATION

### A. Experimental Setup and Evaluation Corpus
We conducted a comprehensive empirical evaluation of **ClinGap-NLP** on an independent held-out synthetic test cohort of $N = 600$ clinical records (random seed = 42). To assess cross-specialty robustness, the corpus was stratified equally across 10 major medical specialties (60 notes each): Internal Medicine, Cardiology, Pulmonology, Endocrinology, Gastroenterology, Neurology, Nephrology, Pediatrics, Geriatrics, and Oncology. 

The evaluation suite incorporates 12 distinct clinical scenario archetypes (50 notes each), including acute symptomatic omissions, chronic metabolic monitoring gaps, explicitly unperformed or cancelled investigations, partially satisfied guidelines, completed investigations, active orders awaiting results, clausal and coordinated negations, historical/resolved conditions, and boundary cases with lab units and generic procedure terminology. The test cohort establishes a ground-truth distribution of 250 positive gap cases (prevalence: 41.67%) and 350 compliant or non-indicated cases (58.33%). 

*Methodological Transparency and Benchmark Disclosure:* Ground-truth annotations were established programmatically following deterministic clinical guideline logic, completely segregated from runtime pipeline predictions. Development data ($N = 200$) was maintained in a separate split. Analysis of text diversity indicates 558 unique narratives out of 600 in the test set (42 template-level duplicates across different specialties due to combinatorial demographic sampling) and 25 exact text overlaps between development and test sets. We explicitly disclose that this benchmark represents a controlled synthetic evaluation, not an external multi-annotator clinical audit or real-world EHR validation.

### B. Clinical Decision Gap Detection Performance
Against the 600 held-out test notes, ClinGap-NLP achieved an overall accuracy of **67.50%** (95% CI: [63.65%, 71.13%]), a sensitivity (recall) of **80.00%** (95% CI: [74.60%, 84.49%]), a precision of **57.97%** (95% CI: [52.70%, 63.06%]), and an F1-score of **67.23%**. Specificity was **58.57%** (95% CI: [53.34%, 63.61%]), corresponding to a False Positive Rate (FPR) of **41.43%** and a False Negative Rate (FNR) of **20.00%**.

The confusion matrix comprises:
- **True Positives (TP):** **200** (correctly identified clinical decision omissions)
- **True Negatives (TN):** **205** (correctly identified guideline compliance)
- **False Positives (FP):** **145** (spurious gap alerts)
- **False Negatives (FN):** **50** (unflagged omissions)

### C. Sub-Component Empirical Evaluation
1) *Clinical Negation Detection:* Evaluated across $N = 785$ annotated clinical mentions, the clausal negation module achieved **95.03%** accuracy (95% CI: [93.26%, 96.38%]), **100.00%** precision (TP = 200, FP = 0), **83.68%** recall (FN = 39, TN = 546), an F1-score of **91.12%**, and **100.00%** specificity. The zero False Positive rate confirms that affirmed clinical symptoms and diseases are never incorrectly silenced.

2) *Investigation Status Classification:* Across 350 explicit diagnostic investigation mentions in the test text, the 4-class status classifier achieved an overall multi-class accuracy of **88.86%** (311 / 350 exact diagonal matches). Class-level breakdown:
   - *`completed/performed` (Support = 200):* Precision = **100.00%** (185/185), Recall = **92.50%** (185/200), F1-Score = **96.10%** (15 mentions misclassified as `ordered`).
   - *`pending` (Support = 50):* Precision = **100.00%** (26/26), Recall = **52.00%** (26/50), F1-Score = **68.42%** (24 mentions misclassified as `ordered`).
   - *`not performed` (Support = 100):* Precision = **100.00%** (100/100), Recall = **100.00%** (100/100), F1-Score = **100.00%**.
   - *`ordered` (Support = 0):* This class had zero ground-truth support in the test set. It received 39 predicted false assignments (15 from `completed`, 24 from `pending`). Precision is 0.00% (0/39), while Recall and F1-score are **Undefined (N/A due to zero support)**.
   - *Macro-Averaged F1:* Across the three supported classes, the macro-averaged F1-score was **88.17%** (Macro Precision: 100.00%, Macro Recall: 81.50%).

3) *Clinical Named Entity Recognition (NER):* The hybrid NER architecture achieved an overall micro-averaged F1 of **68.99%** (Precision: 55.23%, Recall: 91.84%) across 2,772 candidate spans. Across the 6 supported clinical categories, the macro-averaged F1 was **83.81%**:
   - *Medication:* Precision = 100.00%, Recall = 93.46%, F1 = **96.62%** (Support = 107)
   - *Dosing Frequency:* Precision = 100.00%, Recall = 94.00%, F1 = **96.91%** (Support = 100)
   - *Disease:* Precision = 93.22%, Recall = 91.67%, F1 = **92.44%** (Support = 600)
   - *Dosage Strength:* Precision = 71.94%, Recall = 100.00%, F1 = **83.68%** (Support = 100)
   - *Symptom:* Precision = 72.01%, Recall = 82.20%, F1 = **76.77%** (Support = 410)
   - *Investigation:* Precision = 39.59%, Recall = 100.00%, F1 = **56.73%** (Support = 350; broad procedure tokens tagged by transformer are filtered downstream)
   *(Note: Categories `DURATION` and `LAB_TEST` had zero ground-truth support in this benchmark.)*

### D. Computational Efficiency and Latency
Timing logs recorded across all 600 full pipeline executions demonstrated an average inference latency of **116.62 ms per note** (median: **97.42 ms**; 95th percentile: **129.50 ms**; minimum: 66.88 ms; cold-start maximum: 10,730.85 ms) on standard CPU hardware. Total cohort execution wall-clock time was **70.02 seconds** (8.57 notes/second), confirming technical viability for interactive clinical decision support.

### E. Error Analysis
Qualitative error analysis of the 145 False Positives and 50 False Negatives revealed key structural insights:
1. *Coarse Guideline Triggers (FP, ~31%):* Prototype Rule R2 configures `{'entities': ['DISEASE']} -> HbA1c`. In non-metabolic chronic diseases (e.g., essential hypertension, migraine, osteoarthritis), Rule R2 triggered and recommended HbA1c, producing 45 False Positives against clinical ground truth.
2. *Historical/Resolved Illnesses (FP, ~35%):* Mentions of remote, resolved conditions (e.g., "resolved diabetes 9 years ago") were extracted as active diseases due to the absence of temporal assertion classifiers.
3. *Disjunctive Negation Syntax (FN, 100% of FNs):* In notes stating *"routine HbA1c was not documented or ordered"*, the trailing keyword *"ordered"* matched the active-order regex pattern, causing the status classifier to assign `status: ordered`. Because active orders legitimately suppress missing gaps, the actual omission was masked, resulting in all 50 False Negatives.

### F. Limitations and Threats to Validity
1. *Synthetic Data Constraint:* Synthetic notes, while diverse, lack the noisy abbreviations, typographical errors, and non-standard syntax prevalent in real-world EHRs. These findings prove computational feasibility, not real-world clinical safety.
2. *Architectural Separation of Components:* ClinGap-NLP couples neural token extraction (`d4data/biomedical-ner-all`) and dense representations (`Bio_ClinicalBERT`) with deterministic, rule-based guideline execution. The embedding is dense semantic representation only and does not perform clinical reasoning.
3. *Prototype Rule Scope:* The knowledge base contains educational demonstration rules. ClinGap-NLP does not provide medical diagnoses or validated clinical care recommendations.
