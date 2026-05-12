"""Curated clinical evaluation dataset.

Each case has a question and a list of 'gold' source IDs that a strong system
should retrieve and cite. Source IDs are PMIDs (PubMed) or NCT IDs (trials).
"""

from pydantic import BaseModel


class EvalCase(BaseModel):
    id: str
    question: str
    expected_sources: list[str]  # PMIDs or NCT IDs of landmark studies
    notes: str = ""


DATASET: list[EvalCase] = [
    EvalCase(
        id="sglt2_hfpef",
        question="Are SGLT2 inhibitors effective for heart failure with preserved ejection fraction?",
        expected_sources=["NCT03057951", "NCT03619213"],  # EMPEROR-Preserved, DELIVER
        notes="Landmark RCTs: EMPEROR-Preserved (empagliflozin), DELIVER (dapagliflozin)",
    ),
    EvalCase(
        id="glp1_obesity",
        question="What is the evidence for semaglutide in adults with obesity but without diabetes?",
        expected_sources=["NCT03548935", "NCT03548987"],  # STEP 1, STEP 2
        notes="STEP trials series",
    ),
    EvalCase(
        id="metformin_b12",
        question="Does long-term metformin use cause vitamin B12 deficiency?",
        expected_sources=["NCT00004992"],  # DPPOS
        notes="Diabetes Prevention Program Outcomes Study",
    ),
    EvalCase(
        id="statins_primary",
        question="Should statins be used for primary prevention of cardiovascular disease in low-risk adults?",
        expected_sources=["NCT00239681"],  # JUPITER
        notes="JUPITER trial",
    ),
    EvalCase(
        id="aspirin_primary",
        question="Is aspirin recommended for primary prevention of cardiovascular events in older adults without diabetes?",
        expected_sources=["NCT01038583"],  # ASPREE
        notes="ASPREE trial",
    ),
    EvalCase(
        id="finerenone_ckd",
        question="What is the role of finerenone in chronic kidney disease with type 2 diabetes?",
        expected_sources=["NCT02540993", "NCT02545049"],  # FIDELIO-DKD, FIGARO-DKD
        notes="FIDELIO-DKD, FIGARO-DKD",
    ),
    EvalCase(
        id="tirzepatide_t2d",
        question="How effective is tirzepatide compared to semaglutide for type 2 diabetes?",
        expected_sources=["NCT03987919"],  # SURPASS-2
        notes="SURPASS-2 head-to-head trial",
    ),
    EvalCase(
        id="rivaroxaban_afib",
        question="Is rivaroxaban non-inferior to warfarin for stroke prevention in atrial fibrillation?",
        expected_sources=["NCT00403767"],  # ROCKET-AF
        notes="ROCKET-AF",
    ),
    EvalCase(
        id="pcsk9_ascvd",
        question="Do PCSK9 inhibitors reduce cardiovascular events in patients on maximally tolerated statins?",
        expected_sources=["NCT01764633", "NCT01663402"],  # FOURIER, ODYSSEY OUTCOMES
        notes="FOURIER (evolocumab), ODYSSEY OUTCOMES (alirocumab)",
    ),
    EvalCase(
        id="canagliflozin_ckd",
        question="What is the renal benefit of canagliflozin in patients with type 2 diabetes and chronic kidney disease?",
        expected_sources=["NCT02065791"],  # CREDENCE
        notes="CREDENCE",
    ),
]
