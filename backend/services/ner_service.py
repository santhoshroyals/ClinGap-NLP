"""
ner_service.py – Hybrid NER extraction for ClinGap-NLP.

Architecture (in priority order):
  1. Hugging Face  d4data/biomedical-ner-all  (primary)
  2. spaCy model via ModelManager             (secondary, if loaded)
  3. Clinical-dictionary lookup               (supplementary)
  4. Regex/pattern extraction                 (supplementary)

The HF model is loaded once and cached.  If it fails to load the service
automatically falls back to layers 2-4 without crashing the application.

DISCLAIMER: This service is a research/decision-support tool only.
It does not diagnose patients or constitute medical advice.
"""

import logging
import json
import os
import re
from typing import List, Dict

try:
    from loguru import logger as _loguru_logger
    _LOGURU_AVAILABLE = True
except ImportError:
    _LOGURU_AVAILABLE = False

log = logging.getLogger(__name__)

from .model_manager import ModelManager

# ---------------------------------------------------------------------------
# Knowledge-base vocabulary loaders (unchanged from original)
# ---------------------------------------------------------------------------

VOCAB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'knowledge_base')
if not os.path.exists(VOCAB_PATH):
    VOCAB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'clinngap_nlp', 'knowledge_base')


def load_vocab_dict(name: str) -> Dict[str, str]:
    """Returns a dict mapping lowercase term to its canonical/normalized form."""
    path = os.path.join(VOCAB_PATH, f'{name}.json')
    result: Dict[str, str] = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        canonical = (
                            item.get('id')
                            or item.get('canonical_name')
                            or item.get('name')
                            or ''
                        )
                        synonyms = item.get('synonyms', [])
                        if 'name' in item:
                            result[item['name'].lower()] = canonical
                        if 'canonical_name' in item:
                            result[item['canonical_name'].lower()] = canonical
                        for syn in synonyms:
                            result[syn.lower()] = canonical
                    elif isinstance(item, str):
                        result[item.lower()] = item.lower()
    return result


def load_vocab(name: str) -> List[str]:
    """Legacy helper for backward compatibility with external imports."""
    return list(load_vocab_dict(name).keys())


MEDICATIONS_DICT = load_vocab_dict('medications')
INVESTIGATIONS_DICT = load_vocab_dict('investigations')
SYMPTOMS_DICT = load_vocab_dict('symptoms')
DISEASES_DICT = load_vocab_dict('diseases')

SUPPLEMENTAL_INVESTIGATIONS: Dict[str, str] = {
    'ecg': 'ecg', 'electrocardiogram': 'ecg', 'ekg': 'ecg',
    'trop-i': 'trop-i', 'troponin-i': 'trop-i', 'troponin': 'trop-i',
    'echo': 'echo', 'echocardiogram': 'echo', 'echocardiography': 'echo', '2d echo': 'echo',
    'angiogram': 'angiogram', 'coronary angiogram': 'angiogram', 'angiography': 'angiogram',
    'endoscopy': 'endoscopy', 'upper gi endoscopy': 'endoscopy', 'ugie': 'endoscopy', 'gastroscopy': 'endoscopy',
    'cbc': 'cbc', 'complete blood count': 'cbc', 'hemogram': 'cbc',
    'x-ray': 'x-ray', 'chest x-ray': 'x-ray', 'cxr': 'x-ray', 'chest xray': 'x-ray', 'xray': 'x-ray',
    'ct': 'ct', 'ct scan': 'ct', 'ct brain': 'ct', 'hrct': 'ct',
    'mri': 'mri', 'mri brain': 'mri',
    'pet scan': 'pet scan', 'pet-ct': 'pet scan',
    'mammogram': 'mammogram', 'mammography': 'mammogram',
    'biopsy': 'biopsy', 'tru-cut biopsy': 'biopsy', 'fnac': 'biopsy',
    'stool': 'stool', 'stool routine': 'stool', 'stool examination': 'stool',
    'crp': 'crp', 'c-reactive protein': 'crp',
    'hba1c': 'hba1c', 'glycated hemoglobin': 'hba1c',
    'usg': 'ultrasound', 'ultrasound': 'ultrasound',
}

SUPPLEMENTAL_SYMPTOMS: Dict[str, str] = {
    'palpitations': 'palpitations',
    'dizziness': 'dizziness',
    'irregular heartbeat': 'irregular heartbeat',
    'syncope': 'syncope',
    'fever': 'fever',
    'high fever': 'high fever',
    'cough': 'cough',
    'productive cough': 'productive cough',
    'hemoptysis': 'hemoptysis',
    'abdominal pain': 'abdominal pain',
    'chest pain': 'chest pain',
    'headache': 'headache',
    'fatigue': 'fatigue',
    'weakness': 'weakness',
    'right side weakness': 'right side weakness',
    'facial droop': 'facial droop',
    'photophobia': 'photophobia',
    'migraine-like': 'migraine-like',
    'bolne mein difficulty': 'speech difficulty',
    'saans lene mein takleef': 'dyspnea',
    'dard ho raha tha': 'pain',
    'loose motions': 'diarrhea',
    'vomiting': 'vomiting',
    'rash': 'rash',
    'measles-like rash': 'measles-like rash',
    'unexplained weight loss': 'weight loss',
    'lump in the breast': 'breast lump',
    'improvement': 'improvement',
}

SUPPLEMENTAL_DISEASES: Dict[str, str] = {
    'coronary artery disease': 'coronary artery disease', 'cad': 'coronary artery disease',
    'nstemi': 'nstemi', 'stemi': 'stemi', 'myocardial infarction': 'myocardial infarction',
    'atrial fibrillation': 'atrial fibrillation', 'afib': 'atrial fibrillation',
    'hypertension': 'hypertension', 'high blood pressure': 'hypertension', 'htn': 'hypertension',
    'diabetes': 'diabetes mellitus', 'diabetes mellitus': 'diabetes mellitus', 't2dm': 'diabetes mellitus',
    'acute gastritis': 'acute gastritis', 'gastritis': 'gastritis',
    'gerd': 'gerd', 'gastroesophageal reflux disease': 'gerd',
    'community-acquired pneumonia': 'community-acquired pneumonia', 'pneumonia': 'pneumonia',
    'ischemic stroke': 'ischemic stroke', 'stroke': 'stroke',
    'epilepsy': 'epilepsy',
    'migraine': 'migraine',
    'carcinoma of the breast': 'breast cancer', 'breast cancer': 'breast cancer',
    'metastatic adenocarcinoma of unknown primary': 'metastatic adenocarcinoma',
    'acute gastroenteritis': 'acute gastroenteritis', 'gastroenteritis': 'acute gastroenteritis',
    'recent uri': 'upper respiratory tract infection', 'uri': 'upper respiratory tract infection',
    'viral exanthem': 'viral exanthem',
    'asthma': 'asthma',
}

SUPPLEMENTAL_MEDICATIONS: Dict[str, str] = {
    'amoxicillin 500mg': 'amoxicillin', 'amoxicillin': 'amoxicillin',
    'clopidogrel 75mg': 'clopidogrel', 'clopidogrel': 'clopidogrel',
    'aspirin 75mg': 'aspirin', 'aspirin 150mg': 'aspirin', 'aspirin': 'aspirin',
    'iv thrombolysis': 'thrombolysis', 'thrombolysis': 'thrombolysis',
    'antiarrhythmics': 'antiarrhythmic',
    'metformin': 'metformin', 'lisinopril': 'lisinopril', 'ibuprofen': 'ibuprofen', 'salbutamol': 'salbutamol',
}

SUPPLEMENTAL_LAB_TESTS: Dict[str, str] = {
    'st elevation': 'st elevation', 'st depression': 'st depression',
    'ef 46%': 'ef 46%', 'ef 47%': 'ef 47%',
    '77% blockage in lad': '77% blockage in lad',
    'wbc high': 'wbc high', 'wbc elevated': 'wbc elevated',
    'left mca infarct': 'left mca infarct',
    'no bleed': 'no bleed',
    'no parasites': 'no parasites',
    'anemia': 'anemia',
    'metastasis': 'metastasis',
    'malignancy': 'malignancy',
}

INVESTIGATIONS_DICT.update(SUPPLEMENTAL_INVESTIGATIONS)
SYMPTOMS_DICT.update(SUPPLEMENTAL_SYMPTOMS)
DISEASES_DICT.update(SUPPLEMENTAL_DISEASES)
MEDICATIONS_DICT.update(SUPPLEMENTAL_MEDICATIONS)
LAB_TESTS_DICT = load_vocab_dict('lab_tests')
LAB_TESTS_DICT.update(SUPPLEMENTAL_LAB_TESTS)

DOSAGE_PATTERN = re.compile(
    r'\b\d+(?:\.\d+)?\s*(?:mg|g|ml|mL|units|mcg|µg)(?!\s*/\s*(?:d[lL]|[lL]|m[lL]|u[lL]|µ[lL]|mm3|kg|min|hr|h|day)|%)\b',
    re.I
)
FREQ_PATTERN = re.compile(
    r'\b(?:'
    r'every\s+\d+\s+(?:hours?|days?|weeks?)|'
    r'once\s+daily|twice\s+daily|'
    r'three\s+times\s+daily|four\s+times\s+daily|'
    r'once\s+weekly|twice\s+weekly|once\s+monthly|'
    r'\d+\s+times?\s+(?:a|per)\s+day|'
    r'as\s+needed|'
    r'daily|weekly|monthly|'
    r'q\d+h|bid|tid|qid|od|bd|qd|qhs|prn'
    r')\b',
    re.I
)


def _is_lab_measurement_or_non_medication(word: str) -> bool:
    """Return True if word is a numeric lab measurement, vital sign, or non-medication string."""
    cleaned = word.strip().lower()
    if re.search(r'\d', cleaned) and re.search(
        r'(?:mg/d[lL]|g/d[lL]|mmol/[lL]|µmol/[lL]|mEq/[lL]|mmhg|bpm|beats|°c|%|/d[lL]|/min|/hr)',
        cleaned,
        re.I
    ):
        return True
    if re.match(r'^\d+(?:\.\d+)?\s*(?:mg|g|ml|mcg|µg|units)?\s*(?:/[a-z0-9]+)?$', cleaned, re.I):
        return True
    return False


GENERIC_INVESTIGATION_WORDS: frozenset = frozenset({
    'test', 'tests',
    'investigation', 'investigations',
    'procedure', 'procedures',
    'exam', 'examination', 'examinations',
    'study', 'studies',
    'workup', 'workups',
    'panel', 'panels',
    'screen', 'screening', 'screenings',
    'profile', 'profiles',
    'evaluation', 'evaluations',
    'assessment', 'assessments',
    'diagnostic test', 'diagnostic tests',
    'lab test', 'lab tests',
    'laboratory test', 'laboratory tests',
})

# False positive filter sets
ADMIN_ID_PATTERN = re.compile(
    r'^(?:'
    r'\d{5,}|'                                                 # Pure numbers / UHIDs
    r'(?:uhid|adm|ipd|opd|mrn|bed|id|reg|cr|ip)[\s_.:#-]*\d+|'  # Registration codes
    r'class\s+[ivx0-9]+|'                                      # Modified Kuppuswamy / NYHA class
    r'grade\s+[ivx0-9]+|'                                      # Grading
    r'stage\s+[ivx0-9]+|'                                      # Staging
    r'type\s+[ivx0-9]+'                                        # Isolated Type I/II
    r')$',
    re.IGNORECASE
)

NON_LAB_CONDITION_WORDS: frozenset = frozenset({
    'stable', 'unstable', 'critical', 'guarded', 'fair', 'poor',
    'satisfactory', 'improved', 'deteriorated', 'deceased', 'moribund',
    'status post', 'post-op', 'pre-op',
})

SECTION_HEADING_WORDS: frozenset = frozenset({
    'physical examination', 'physical exam', 'general examination', 'systemic examination',
    'local examination', 'clinical examination',
    'condition at discharge', 'condition on discharge', 'condition',
    'discharge summary', 'admission summary', 'summary',
    'history of present illness', 'chief complaint', 'chief complaints',
    'past history', 'family history', 'personal history', 'social history',
    'course in hospital', 'hospital course', 'advice on discharge',
    'follow up', 'follow-up', 'treatment given', 'investigations / lab results',
    'treating consultant', 'consultant', 'attending physician',
    'cardiology', 'general_medicine', 'general medicine', 'oncology', 'pediatrics',
    'neurology', 'gastroenterology', 'nephrology', 'pulmonology', 'orthopedics',
    'dermatology', 'psychiatry', 'urology', 'department', 'ward', 'icu', 'ccu',
    'hospital', 'nethralaya', 'clinic', 'institute', 'centre', 'center',
    'rhythm', 'zinc',
})

NON_SYMPTOM_WORDS: frozenset = frozenset({
    # Hindi / Hinglish non-symptom words & stop words
    'bahut', 'bhi', 'aur', 'tha', 'thi', 'the', 'hai', 'hain', 'ko', 'se',
    'ke', 'ka', 'ki', 'mein', 'me', 'par', 'ho', 'raha', 'rahi', 'rahe',
    'kuch', 'koi', 'nahi', 'nahin', 'halka', 'halki', 'jyada', 'zyada', 'kam',
    'ek', 'do', 'teen', 'din', 'mahina', 'saal',
    # Incomplete isolated fragment words
    'difficulty',
})


def extract_investigation_status(text: str, ent_text: str, is_negated: bool = False) -> str:
    """
    Determine the clinical status of an investigation mention:
      'ORDERED/PENDING', 'pending', 'ordered', 'completed/performed', 'not performed'
    """
    clauses = re.split(r'[.\n;]', text)
    matching_clause = ''
    for cl in clauses:
        if re.search(rf'\b{re.escape(ent_text)}\b', cl, re.I):
            matching_clause = cl
            break

    if not matching_clause:
        matching_clause = text

    # 1. Ordered / Requested but not yet performed -> ORDERED/PENDING
    is_ordered_or_requested = bool(re.search(
        r'\b(?:was\s+ordered|is\s+ordered|has\s+been\s+ordered|has\s+been\s+requested|'
        r'was\s+requested|requested|ordered|to\s+be\s+ordered|to\s+order|will\s+order|'
        r'scheduled\s+for|send\s+for|sent\s+for|requisitioned)\b',
        matching_clause,
        re.I
    ))
    has_not_yet_performed = bool(re.search(
        r'\b(?:not\s+yet\s+(?:been\s+)?(?:performed|done|taken|obtained|completed|conducted)|'
        r'has\s+not\s+yet\s+been\s+(?:performed|done|taken|obtained|completed|conducted)|'
        r'yet\s+to\s+be\s+(?:performed|done|completed)|'
        r'pending\s+(?:performance|completion|results?)|'
        r'awaiting\s+(?:performance|completion|results?))\b',
        matching_clause,
        re.I
    ))

    if is_ordered_or_requested and has_not_yet_performed:
        return 'ORDERED/PENDING'

    # 2. Pending checks (awaiting results / not yet available)
    if re.search(
        r'\b(?:not\s+yet\s+available|not\s+available\s+yet|awaiting\s+results?|'
        r'results?\s+(?:are\s+|is\s+)?pending|pending\s+results?|\bpending\b|'
        r'in\s+progress|not\s+yet\s+back|awaited|result\s+awaited)\b',
        matching_clause,
        re.I
    ):
        return 'pending'

    # 3. Explicitly cancelled or not performed (without active order)
    if is_negated or re.search(
        r'\b(?:was\s+not\s+(?:performed|done|taken|obtained|completed|conducted)|'
        r'not\s+(?:been\s+)?(?:performed|done|taken|obtained|completed|conducted)|'
        r'has\s+not\s+been\s+(?:performed|done|taken|obtained|completed|conducted)|'
        r'not\s+carried\s+out|declined|refused|cancelled|discontinued|omitted)\b',
        matching_clause,
        re.I
    ):
        return 'not performed'

    # 4. Completed / Performed checks
    # Action verbs
    if re.search(
        r'\b(?:completed|was\s+performed|performed|was\s+done|done|showed|shows|revealed|'
        r'revealing|demonstrates?|demonstrating|noted|seen|observed|'
        r'result(?:s)?\s+(?:show|showed|is|was|of|were|revealed))\b',
        matching_clause,
        re.I
    ):
        return 'completed/performed'

    # Measurements / units (e.g. 77% blockage, EF 46%, 120/80 mmHg)
    if re.search(r'(?:\blevel\s+of|\d+(?:\.\d+)?\s*(?:mg/d[lL]|mmol/[lL]|°c|%|mmHg|beats|/min)(?!\w))', matching_clause, re.I):
        return 'completed/performed'

    # Direct colon findings: e.g. "ECG: ST elevation", "Echo: EF 46%", "Trop-I: Positive", "Biopsy: malignancy"
    colon_m = re.search(rf'\b{re.escape(ent_text)}\b\s*:\s*([^\n;]+)', matching_clause, re.I)
    if colon_m:
        finding = colon_m.group(1).strip()
        if not re.search(r'^(?:ordered|pending|awaited|to\s+order|scheduled)\b', finding, re.I):
            return 'completed/performed'

    # Result keywords anywhere in the clause
    if re.search(
        r'\b(?:positive|negative|normal|abnormal|elevated|high|low|infarct|blockage|'
        r'stenosis|mass|malignan(?:t|cy)|carcinoma|parasites|consolidation|effusion|'
        r'st\s+elevation|st\s+depression|t\s+wave|sinus\s+rhythm|afib|ischemi(?:a|c)|'
        r'no\s+(?:bleed|acute|parasites|mass|lesion|abnormality|fracture|growth))\b',
        matching_clause,
        re.I
    ):
        return 'completed/performed'

    # 5. Ordered / Requested without completed results
    if is_ordered_or_requested:
        return 'ordered'

    return 'ordered'

# ---------------------------------------------------------------------------
# Hugging Face model – lazy singleton
# ---------------------------------------------------------------------------

# Maps d4data/biomedical-ner-all entity_group → ClinGap entity_type.
# Only labels that are meaningful for the ClinGap decision-gap pipeline are
# listed here.  Everything else is silently ignored.
_HF_LABEL_MAP: Dict[str, str] = {
    'Disease_disorder':     'DISEASE',
    'Sign_symptom':         'SYMPTOM',
    'Medication':           'MEDICATION',
    'Diagnostic_procedure': 'INVESTIGATION',
    'Dosage':               'DOSAGE',
    'Frequency':            'FREQUENCY',
    'Duration':             'DURATION',
    'Lab_value':            'LAB_TEST',
}

# Noise-word filter: generic words that are never clinical entities regardless
# of model confidence.  Keep this short – NOT meant to enumerate medical terms.
_NOISE_TOKENS: frozenset = frozenset({
    # Stop words / connectors
    'or', 'and', 'the', 'a', 'an', 'of', 'in', 'to', 'is', 'was',
    'be', 'are', 'for', 'by', 'on', 'at', 'as', 'with', 'it', 'its',
    'she', 'he', 'they', 'we', 'her', 'his', 'this', 'that', 'which',
    'also', 'then', 'than', 'both', 'only', 'been', 'has', 'had',
    # WordPiece stubs
    't', 'z', 's', 're', 'ed', 've', 'll', 'no', 'not',
    # Generic single-concept words the model over-tags
    'one', 'two', 'three', 'all', 'last', 'first', 'next',
    'summer', 'spring', 'winter', 'fall', 'autumn',
    'daily', 'medication', 'medications', 'medicine', 'medicines', 'drug', 'drugs', 'spray', 'sprays',
    'test', 'tests', 'investigation', 'investigations', 'procedure', 'procedures', 'exam', 'examination', 'workup', 'study', 'studies',
    # Document title and header noise
    'clingap', 'nlp test', 'clinical note',
})

# Minimum confidence threshold for HF entities
_MIN_CONFIDENCE: float = 0.60

# Minimum meaningful entity length (characters)
_MIN_ENTITY_LEN: int = 4

_hf_ner_pipeline = None         # cached pipeline instance
_hf_load_attempted: bool = False  # ensures we only try once


def _load_hf_pipeline():
    """
    Lazily loads the d4data/biomedical-ner-all pipeline exactly once.
    Returns the pipeline object, or None if loading failed.
    """
    global _hf_ner_pipeline, _hf_load_attempted
    if _hf_load_attempted:
        return _hf_ner_pipeline

    _hf_load_attempted = True
    try:
        from transformers import pipeline as hf_pipeline
        log.info(
            "Loading Hugging Face NER model 'd4data/biomedical-ner-all' "
            "(CPU, first-time load may take a few seconds)..."
        )
        _hf_ner_pipeline = hf_pipeline(
            "token-classification",
            model="d4data/biomedical-ner-all",
            aggregation_strategy="simple",
            device=-1,  # CPU only; safe when CUDA is not available
        )
        log.info("Hugging Face NER model loaded successfully.")
    except Exception as exc:
        log.warning(
            "Failed to load Hugging Face NER model 'd4data/biomedical-ner-all': %s. "
            "Falling back to spaCy / dictionary / regex NER.",
            exc,
        )
        _hf_ner_pipeline = None

    return _hf_ner_pipeline


def _is_wordpiece_artifact(text: str) -> bool:
    """Returns True for obvious un-merged WordPiece fragments like '##ing'."""
    return text.startswith('##')


def _is_boundary_fragment(surface: str, start: int, end: int, source_text: str) -> bool:
    """
    Returns True when the span begins or ends in the middle of an alphanumeric word
    in the source text — a telltale sign of a BERT chunk-boundary artifact or
    subword tokenization fragment (e.g. 'hyper' in 'hypertension' or 'tho' in 'Ortho').
    """
    if start is not None and start > 0 and source_text[start - 1].isalnum():
        return True
    if end is not None and end < len(source_text) and source_text[end].isalnum():
        return True
    return False


def _is_noisy_entity(word: str) -> bool:
    """Returns True for tokens that should never be accepted as entities."""
    cleaned = word.strip().rstrip('.,;:').lower()
    # Clinical dictionary terms are legitimate entities (even if short like CBC or A1C or CT or MRI)
    if (
        cleaned in INVESTIGATIONS_DICT
        or cleaned in MEDICATIONS_DICT
        or cleaned in DISEASES_DICT
        or cleaned in SYMPTOMS_DICT
        or cleaned in LAB_TESTS_DICT
    ):
        return False
    if cleaned in _NOISE_TOKENS or cleaned in GENERIC_INVESTIGATION_WORDS or cleaned in SECTION_HEADING_WORDS:
        return True
    if len(cleaned) < _MIN_ENTITY_LEN:
        return True
    if _is_wordpiece_artifact(cleaned):
        return True
    return False


def _extract_hf_entities(text: str) -> List[Dict]:
    """
    Run the HF pipeline on *text* and return a list of ClinGap-formatted
    entity dicts for labels that are in _HF_LABEL_MAP only.
    """
    pipe = _load_hf_pipeline()
    if pipe is None:
        return []

    entities: List[Dict] = []
    try:
        # stride=128 creates overlapping windows for long texts so that
        # entities near the 512-token boundaries are not split/truncated.
        raw = pipe(text, stride=128)
    except Exception as exc:
        log.warning("Hugging Face NER inference failed: %s", exc)
        return []

    for item in raw:
        label = item.get('entity_group', '')
        score = float(item.get('score', 0.0))
        word  = str(item.get('word', '')).strip()

        # Map only the labels we care about
        clingap_type = _HF_LABEL_MAP.get(label)
        if clingap_type is None:
            continue

        # Confidence filter
        if score < _MIN_CONFIDENCE:
            continue

        # Recover original casing from the source text using char offsets.
        # The HF pipeline tokenizer lowercases internally; start/end point
        # back to the original characters so we can restore the surface form.
        start = item.get('start')
        end   = item.get('end')
        if start is not None and end is not None:
            surface = text[start:end].strip()
            if surface:
                word = surface

        # Reject chunk-boundary artifacts and subword fragments (e.g. 'hyper' in 'hypertension')
        if _is_boundary_fragment(word, start, end, text):
            continue

        clean_word = word.strip().rstrip('.,;:').lower()

        # Reject pure digits for clinical entities
        if re.match(r'^\d+$', clean_word):
            continue

        # Reject administrative IDs and scale ratings
        if ADMIN_ID_PATTERN.match(clean_word):
            continue

        # Specific LAB_TEST false positive filters
        if clingap_type == 'LAB_TEST':
            if clean_word in NON_LAB_CONDITION_WORDS:
                continue

        # Specific INVESTIGATION false positive filters: section headings, departments, generic labels
        if clingap_type == 'INVESTIGATION':
            if clean_word in SECTION_HEADING_WORDS or clean_word in GENERIC_INVESTIGATION_WORDS:
                continue
            if re.match(r'^(?:department|dr|doctor|prof|ward|clinic)\b', clean_word):
                continue
            if start is not None and re.search(r'(?:^|\n)\s*' + re.escape(word) + r'\s*:', text[:end + 2], re.I):
                continue

        # Specific SYMPTOM false positive filters: common Hindi words, isolated non-symptoms
        if clingap_type == 'SYMPTOM':
            if clean_word in NON_SYMPTOM_WORDS:
                continue

        # Noise / fragment filter (applied after casing recovery)
        if _is_noisy_entity(word):
            continue

        # Reject generic standalone investigation words
        if clingap_type == 'INVESTIGATION' and clean_word in GENERIC_INVESTIGATION_WORDS:
            continue

        # Clinical dictionary investigation override:
        # If the extracted entity matches an investigation in our knowledge base (e.g. HbA1c),
        # force its type to INVESTIGATION regardless of what the HF model predicted (e.g. Medication).
        if clean_word in INVESTIGATIONS_DICT:
            clingap_type = 'INVESTIGATION'
        elif clean_word in LAB_TESTS_DICT and clingap_type not in {'INVESTIGATION', 'MEDICATION', 'DOSAGE'}:
            clingap_type = 'LAB_TEST'

        if clingap_type == 'DOSAGE':
            freq_m = FREQ_PATTERN.search(word)
            dose_m = DOSAGE_PATTERN.search(word)
            if dose_m:
                dosage_word = dose_m.group(0).strip()
                entities.append({
                    'entity_text':      dosage_word,
                    'entity_type':      'DOSAGE',
                    'normalized_value': dosage_word.lower(),
                    'confidence':       round(score, 4),
                    'source':           'Hugging Face Biomedical NER',
                    'negated':          False,
                })
                if freq_m:
                    freq_word = freq_m.group(0).strip()
                    entities.append({
                        'entity_text':      freq_word,
                        'entity_type':      'FREQUENCY',
                        'normalized_value': freq_word.lower(),
                        'confidence':       round(score, 4),
                        'source':           'Hugging Face Biomedical NER',
                        'negated':          False,
                    })
                continue

        if clingap_type == 'MEDICATION' and _is_lab_measurement_or_non_medication(clean_word):
            continue
        if clingap_type == 'DOSAGE' and _is_lab_measurement_or_non_medication(clean_word):
            continue

        norm_val = INVESTIGATIONS_DICT.get(clean_word, word.lower()) if clingap_type == 'INVESTIGATION' else word.lower()
        entities.append({
            'entity_text':      word,
            'entity_type':      clingap_type,
            'normalized_value': norm_val,
            'confidence':       round(score, 4),
            'source':           'Hugging Face Biomedical NER',
            'negated':          False,  # Negation is handled by negation_service
        })

    return entities


# ---------------------------------------------------------------------------
# Main hybrid NER function (public API – unchanged signature)
# ---------------------------------------------------------------------------

def hybrid_ner(text: str) -> List[Dict]:
    """
    Extract clinical entities from *text* using a four-layer hybrid approach:

      Layer 1 - Hugging Face d4data/biomedical-ner-all (primary)
      Layer 2 - spaCy model via ModelManager (if available)
      Layer 3 - Clinical-dictionary lookup
      Layer 4 - Regex/pattern extraction (dosage, frequency)

    Returns a deduplicated list of entity dicts with the ClinGap schema:
      entity_text, entity_type, normalized_value, confidence, source, negated
    """
    entities: List[Dict] = []
    occupied_spans: List[tuple] = []

    # ------------------------------------------------------------------
    # Layer 1: Hugging Face biomedical NER (primary)
    # ------------------------------------------------------------------
    hf_entities = _extract_hf_entities(text)
    for ent in hf_entities:
        # Track occupied spans so dictionary/regex don't duplicate them.
        word = ent['entity_text']
        m = re.search(re.escape(word), text, re.I)
        if m:
            occupied_spans.append((m.start(), m.end()))
        entities.append(ent)

    # ------------------------------------------------------------------
    # Layer 2: spaCy NER via ModelManager (secondary / optional)
    # ------------------------------------------------------------------
    ner_model = ModelManager.load_ner()
    if ner_model:
        doc = ner_model(text)
        for ent in doc.ents:
            span = (ent.start_char, ent.end_char)
            # Skip if already covered by a HF entity
            if any(s[0] <= span[0] and span[1] <= s[1] for s in occupied_spans):
                continue
            occupied_spans.append(span)
            entities.append({
                'entity_text':      ent.text,
                'entity_type':      ent.label_,
                'normalized_value': ent.text.lower(),
                'confidence':       float(ent._.score) if hasattr(ent._, 'score') else 0.95,
                'source':           f'Biomedical NER Model ({ModelManager._ner_model_name})',
                'negated':          False,
            })

    # ------------------------------------------------------------------
    # Layer 3: Clinical-dictionary lookup (supplementary)
    # ------------------------------------------------------------------
    categories = [
        (DISEASES_DICT,       'DISEASE'),
        (INVESTIGATIONS_DICT, 'INVESTIGATION'),
        (MEDICATIONS_DICT,    'MEDICATION'),
        (SYMPTOMS_DICT,       'SYMPTOM'),
        (LAB_TESTS_DICT,      'LAB_TEST'),
    ]

    for vocab_dict, entity_type in categories:
        # Longest match first to prioritize multiword entities
        sorted_terms = sorted(vocab_dict.keys(), key=len, reverse=True)
        for term in sorted_terms:
            pattern = re.compile(rf'\b{re.escape(term)}\b', re.I)
            for m in pattern.finditer(text):
                span = (m.start(), m.end())
                if any(s[0] <= span[0] and span[1] <= s[1] for s in occupied_spans):
                    continue
                occupied_spans.append(span)
                canonical = vocab_dict[term] or term
                entities.append({
                    'entity_text':      m.group(0),
                    'entity_type':      entity_type,
                    'normalized_value': canonical.lower(),
                    'confidence':       0.9,
                    'source':           'Clinical Dictionary (Fallback)',
                    'negated':          False,
                })

    # ------------------------------------------------------------------
    # Layer 4: Regex patterns (dosage, frequency)
    # ------------------------------------------------------------------
    for m in DOSAGE_PATTERN.finditer(text):
        entities.append({
            'entity_text':      m.group(0),
            'entity_type':      'DOSAGE',
            'normalized_value': m.group(0),
            'confidence':       1.0,
            'source':           'Regex/Pattern',
            'negated':          False,
        })

    for m in FREQ_PATTERN.finditer(text):
        entities.append({
            'entity_text':      m.group(0),
            'entity_type':      'FREQUENCY',
            'normalized_value': m.group(0),
            'confidence':       1.0,
            'source':           'Regex/Pattern',
            'negated':          False,
        })

    # ------------------------------------------------------------------
    # High-priority clinical dictionary normalization:
    # Any entity matching an investigation term must be INVESTIGATION with canonical value.
    # Preserve original extraction source!
    # ------------------------------------------------------------------
    for ent in entities:
        clean_text = ent['entity_text'].strip().rstrip('.,;:').lower()
        if clean_text in INVESTIGATIONS_DICT:
            ent['entity_type'] = 'INVESTIGATION'
            ent['normalized_value'] = INVESTIGATIONS_DICT[clean_text]
        elif clean_text in LAB_TESTS_DICT and ent['entity_type'] not in {'INVESTIGATION', 'MEDICATION', 'DOSAGE'}:
            ent['entity_type'] = 'LAB_TEST'
            ent['normalized_value'] = LAB_TESTS_DICT[clean_text]

    # ------------------------------------------------------------------
    # Deduplicate: (entity_text.lower(), entity_type) -> keep highest confidence
    # ------------------------------------------------------------------
    unique: Dict[tuple, Dict] = {}
    for e in entities:
        clean_txt = e['entity_text'].strip().rstrip('.,;:').lower()
        if clean_txt in _NOISE_TOKENS:
            continue
        if re.match(r'^\d+$', clean_txt) and e['entity_type'] != 'DOSAGE':
            continue
        if ADMIN_ID_PATTERN.match(clean_txt):
            continue
        if e['entity_type'] == 'INVESTIGATION' and (clean_txt in SECTION_HEADING_WORDS or clean_txt in GENERIC_INVESTIGATION_WORDS):
            continue
        if e['entity_type'] == 'LAB_TEST' and clean_txt in NON_LAB_CONDITION_WORDS:
            continue
        if e['entity_type'] == 'SYMPTOM' and clean_txt in NON_SYMPTOM_WORDS:
            continue
        # Verify word boundaries in the original text (reject floating subword fragments like 'hyper')
        if not re.search(rf'(?<!\w){re.escape(e["entity_text"].strip())}(?!\w)', text, re.I):
            continue
        key = (e['entity_text'].lower(), e['entity_type'])
        if key not in unique or e['confidence'] > unique[key]['confidence']:
            unique[key] = e

    # ------------------------------------------------------------------
    # Nested entity deduplication:
    # If a shorter entity is strictly nested inside a longer entity of the
    # same/compatible clinical category for ALL of its occurrences in text,
    # suppress the shorter nested duplicate in favor of the longer entity.
    # If there is at least one standalone occurrence outside the longer entity,
    # preserve it.
    # ------------------------------------------------------------------
    candidates = list(unique.values())
    filtered_entities: List[Dict] = []
    clinical_types = {'DISEASE', 'SYMPTOM', 'MEDICATION', 'INVESTIGATION', 'LAB_TEST'}

    for cand in candidates:
        cand_txt = cand['entity_text'].strip()
        cand_type = cand['entity_type']

        # Prevent generic words from becoming standalone investigation entities
        if cand_type == 'INVESTIGATION' and cand_txt.strip().rstrip('.,;:').lower() in GENERIC_INVESTIGATION_WORDS:
            continue
        if cand_type == 'INVESTIGATION' and cand_txt.strip().rstrip('.,;:').lower() in SECTION_HEADING_WORDS:
            continue

        # Only evaluate nested deduplication for clinical entity types
        if cand_type not in clinical_types:
            filtered_entities.append(cand)
            continue

        # Find all standalone spans of this candidate in text
        cand_spans = [
            (m.start(), m.end())
            for m in re.finditer(rf'(?<!\w){re.escape(cand_txt)}(?!\w)', text, re.I)
        ]
        if not cand_spans:
            continue

        # Find longer entities in the same or compatible category
        longer_spans: List[tuple] = []
        for other in candidates:
            if other is cand:
                continue
            other_txt = other['entity_text'].strip()
            other_type = other['entity_type']
            if len(other_txt) <= len(cand_txt):
                continue
            # Compatible categories: same type, or both in {DISEASE, SYMPTOM}
            is_compatible = (
                other_type == cand_type
                or ({other_type, cand_type}.issubset({'DISEASE', 'SYMPTOM'}))
            )
            if not is_compatible:
                continue

            for m in re.finditer(rf'(?<!\w){re.escape(other_txt)}(?!\w)', text, re.I):
                longer_spans.append((m.start(), m.end()))

        # Check if every occurrence of cand is contained within some longer entity span
        all_nested = True
        for cs, ce in cand_spans:
            contained = any(
                ls <= cs and ce <= le and (ls, le) != (cs, ce)
                for ls, le in longer_spans
            )
            if not contained:
                all_nested = False
                break

        if all_nested and longer_spans:
            # Completely nested within longer entity throughout the text: suppress
            continue

        # Final safety check: do not classify a laboratory measurement as a medication or dosage
        if cand_type in {'MEDICATION', 'DOSAGE'} and _is_lab_measurement_or_non_medication(cand_txt):
            continue

        if cand_type == 'INVESTIGATION':
            cand['status'] = extract_investigation_status(text, cand_txt, cand.get('negated', False))

        filtered_entities.append(cand)

    return filtered_entities

