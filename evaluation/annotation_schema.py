"""
annotation_schema.py - Structured Clinical NLP & Guideline Annotation Schema
ClinGap-NLP Evaluation Infrastructure (Phase 3)

Design Principles:
1. Strict separation between Text-Extraction Labels (Layer 1: Entities, Negation, Status)
   and Clinical Guideline Judgments (Layer 2: Guideline Activation, Decision Gaps).
2. Explicit verification status (AWAITING_HUMAN_VERIFICATION vs. EXPERT_VERIFIED).
3. Zero automatic population from system predictions to prevent circular pseudo-validation.
"""

from typing import List, Optional, Literal, Dict, Any, Tuple
from pydantic import BaseModel, Field


# Allowed entity types in ClinGap-NLP ontology
EntityType = Literal[
    "DISEASE",
    "SYMPTOM",
    "MEDICATION",
    "INVESTIGATION",
    "DOSAGE",
    "FREQUENCY",
    "LAB_TEST",
    "PHYSICAL_SIGN",
    "VITAL_SIGN"
]

# Clinical sub-classification of entity spans
ClinicalSubkind = Literal[
    "physical_sign",
    "vital_sign",
    "subjective_symptom",
    "investigation_finding",
    "clinical_course",
    "general"
]

# Finding polarity (+/-, positive, negative, normal, abnormal)
FindingPolarity = Literal[
    "positive",
    "negative",
    "normal",
    "abnormal",
    "neutral",
    "unknown",
    "unspecified"
]

# Clinical investigation execution status
InvestigationStatus = Literal[
    "completed/performed",
    "ordered",
    "pending",
    "not performed/cancelled",
    "undocumented"
]

# Investigation finding categorization
FindingCategory = Literal[
    "normal",
    "abnormal",
    "neutral",
    "unknown",
    "unspecified"
]

# Clinical narrative annotation language
AnnotationLanguage = Literal[
    "en",
    "hinglish",
    "hi"
]

# Verification state of the record
VerificationState = Literal[
    "AWAITING_HUMAN_VERIFICATION",
    "RESEARCHER_ANNOTATED",
    "RESEARCHER_CONSENSUS",
    "EXPERT_VERIFIED",
    "FLAGGED_DISCREPANCY",
    "REJECTED_UNSUITABLE"
]

# Gap clinical severity level
GapSeverity = Literal[
    "critical",
    "moderate",
    "advisory"
]


# ==============================================================================
# LAYER 1: TEXT-EXTRACTION GROUND TRUTH (Linguistic / NLP Spans)
# ==============================================================================

class EntitySpanAnnotation(BaseModel):
    """Ground-truth span for a named clinical entity."""
    start_char: int = Field(..., description="0-indexed start character offset in clinical_note")
    end_char: int = Field(..., description="0-indexed end character offset in clinical_note")
    entity_text: str = Field(..., description="Verbatim text span as written in note")
    entity_type: EntityType = Field(..., description="Ontological entity category")
    clinical_subkind: Optional[ClinicalSubkind] = Field(None, description="Sub-classification (e.g. physical_sign, vital_sign)")
    finding_polarity: Optional[FindingPolarity] = Field(None, description="Documented polarity (+/-, positive, negative, normal, abnormal)")
    normalized_value: Optional[str] = Field(None, description="Canonical normalized terminology (e.g. RxNorm, SNOMED, ICD or standard lowercase)")
    is_uncertain: Optional[bool] = Field(False, description="True if annotation boundary or category is uncertain")
    uncertainty_note: Optional[str] = Field(None, description="Researcher notes regarding uncertainty")


class NegationAnnotation(BaseModel):
    """Ground-truth assertion for clinical finding negation and scope."""
    entity_text: str = Field(..., description="The clinical entity finding being negated or asserted")
    is_negated: bool = Field(..., description="True if finding is negated/denied/absent; False if affirmed/present")
    negation_cue: Optional[str] = Field(None, description="Verbatim lexical cue phrase e.g. 'denies', 'no', 'absence of', 'nahi hai'")
    cue_offsets: Optional[Tuple[int, int]] = Field(None, description="Exact 0-indexed [start_char, end_char] of verbatim negation cue")
    scope_text: Optional[str] = Field(None, description="Surrounding clause or sentence containing the negation scope")
    scope_offsets: Optional[Tuple[int, int]] = Field(None, description="Exact 0-indexed [start_char, end_char] of negation scope")
    language: Optional[AnnotationLanguage] = Field("en", description="Language of clinical expression (en, hinglish, hi)")
    normalized_assertion: Optional[str] = Field(None, description="Normalized clinical assertion e.g. 'absence of syncope', 'lack of improvement'")
    is_uncertain: Optional[bool] = Field(False, description="True if negation scope or cue is ambiguous")
    uncertainty_note: Optional[str] = Field(None, description="Researcher notes regarding negation uncertainty")


class InvestigationStatusAnnotation(BaseModel):
    """Ground-truth classification of diagnostic investigation performance status and findings."""
    investigation_name: str = Field(..., description="Name of the diagnostic test or laboratory investigation")
    status: InvestigationStatus = Field(..., description="Clinical status of the test in this clinical encounter")
    evidence_snippet: Optional[str] = Field(None, description="Text snippet justifying the status classification (e.g. 'results pending', 'was performed')")
    finding_result: Optional[str] = Field(None, description="Documented finding, value, or qualitative result associated with the investigation")
    finding_offsets: Optional[Tuple[int, int]] = Field(None, description="Exact 0-indexed [start_char, end_char] of finding result text in note")
    finding_category: Optional[FindingCategory] = Field(None, description="Categorization of finding (normal, abnormal, neutral, unknown, unspecified)")
    is_uncertain: Optional[bool] = Field(False, description="True if status is ambiguous or borderline")
    uncertainty_note: Optional[str] = Field(None, description="Researcher notes regarding status uncertainty")


# ==============================================================================
# LAYER 2: CLINICAL GUIDELINE & DECISION GAP JUDGMENT (Domain-Expertise)
# ==============================================================================

class GuidelineActivationAnnotation(BaseModel):
    """Ground-truth judgment of whether a clinical guideline rule applies to this patient encounter."""
    guideline_id: str = Field(..., description="Identifier of the guideline rule (e.g. R1, R2, G_T2DM_01)")
    is_triggered: bool = Field(..., description="Whether patient presentation clinically meets rule prerequisite")
    triggering_conditions: List[str] = Field(default_factory=list, description="Specific patient findings satisfying the rule")
    expected_recommendation: Optional[str] = Field(None, description="Required diagnostic or therapeutic action mandated by guideline")
    clinical_rationale: Optional[str] = Field(None, description="Medical rationale for guideline activation or non-activation")


class DecisionGapAnnotation(BaseModel):
    """Ground-truth judgment of an omission, delay, or clinical deviation."""
    gap_type: Literal["MISSING_INVESTIGATION", "UNPERFORMED_ORDERED_TEST", "MEDICATION_OMISSION", "CONTRAINDICATION_WARNING"]
    target_entity: str = Field(..., description="Name of the omitted or missing investigation/medication")
    is_actionable_gap: bool = Field(..., description="True if this omission represents a genuine clinical care gap")
    severity: GapSeverity = Field("moderate", description="Clinical consequence severity")
    justification: Optional[str] = Field(None, description="Clinical reason explaining why this constitutes a gap")


# ==============================================================================
# FULL CASE ANNOTATION DOCUMENT
# ==============================================================================

class CaseAnnotation(BaseModel):
    """Complete multi-layer annotation container for a single clinical record."""
    record_id: int = Field(..., description="Dataset record ID")
    specialty: str = Field(..., description="Medical specialty")
    template_cluster_id: Optional[str] = Field(None, description="Assigned combinatorial narrative cluster ID")
    partition: Literal["train_dev", "validation", "held_out_test"] = Field("held_out_test", description="Dataset split partition")
    clinical_note: str = Field(..., description="Full verbatim clinical note text")

    # Layer 1: Text-extraction annotations
    entities: List[EntitySpanAnnotation] = Field(default_factory=list, description="Verified clinical entity spans")
    negations: List[NegationAnnotation] = Field(default_factory=list, description="Verified negation assertions")
    investigations: List[InvestigationStatusAnnotation] = Field(default_factory=list, description="Verified diagnostic statuses")

    # Layer 2: Clinical guideline and gap annotations
    guidelines: List[GuidelineActivationAnnotation] = Field(default_factory=list, description="Verified guideline activations")
    decision_gaps: List[DecisionGapAnnotation] = Field(default_factory=list, description="Verified clinical decision gaps")

    # Audit & Verification Provenance
    verification_status: VerificationState = Field(
        "AWAITING_HUMAN_VERIFICATION",
        description="Must be RESEARCHER_ANNOTATED or EXPERT_VERIFIED before computing quantitative model metrics"
    )
    annotator_id: Optional[str] = Field(None, description="Identifier of the primary annotator/researcher")
    second_annotator_id: Optional[str] = Field(None, description="Identifier of secondary independent annotator if present")
    annotation_timestamp: Optional[str] = Field(None, description="ISO-8601 timestamp of human annotation")
    reviewer_notes: Optional[str] = Field(None, description="Notes, boundary disputes, or clinical edge-case comments")


class AnnotationBatch(BaseModel):
    """A collection of CaseAnnotation records for batch distribution and review."""
    batch_id: str
    description: str
    created_date: str
    total_cases: int
    cases: List[CaseAnnotation]
