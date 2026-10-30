import streamlit as st
import requests
import os

API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000')

st.set_page_config(page_title='ClinGap-NLP Dashboard', layout='wide')

st.title('ClinGap‑NLP Dashboard')

# Simple navigation
page = st.sidebar.selectbox('Page', ['Home', 'Clinical Input', 'Entity Extraction', 'Guideline Matching', 'Gap Detection', 'Timeline'])

if page == 'Home':
    st.write('Welcome to the ClinGap‑NLP demo. Use the sidebar to navigate.')
elif page == 'Clinical Input':
    st.header('Clinical Document Ingestion')
    input_mode = st.radio('Select Input Mode:', ['Demo Presets', 'MTSamples Dataset', 'Upload Document (.txt, .pdf, .docx)'], horizontal=True)

    default_txt = ""

    if input_mode == 'Demo Presets':
        demo_choice = st.selectbox('Select Demo Case:', [
            'Case 1: Diabetes & Hypertension (Full Note)',
            'Case 2: Diabetes, Metformin & Missing CBC',
            'Case 3: Respiratory Infection & Full Regimen'
        ])
        if 'Case 1' in demo_choice:
            default_txt = "The patient has diabetes mellitus and hypertension. The patient reports increased thirst and frequent urination for the past two weeks. Blood pressure is 150/95 mmHg. HbA1c was performed and the result was 8.2%. CBC was not performed. The patient is taking metformin 500 mg twice daily. The patient was advised to continue medication and follow up after two weeks."
        elif 'Case 2' in demo_choice:
            default_txt = "The patient has diabetes mellitus. CBC was not performed. HbA1c was performed and the result was 8.2%. The patient is taking metformin 500 mg twice daily."
        elif 'Case 3' in demo_choice:
            default_txt = "Patient presents with acute respiratory symptoms and fatigue. Blood pressure noted as high. Aspirin 100 mg once daily was prescribed. Complete blood count (CBC) was not performed during this visit."

    elif input_mode == 'MTSamples Dataset':
        st.subheader('MTSamples Dataset Record')
        col1, col2 = st.columns([1, 3])
        with col1:
            rec_id = st.number_input('MTSamples Record ID (0 - 4965):', min_value=0, max_value=4965, value=3552)
            if st.button('Load Record'):
                try:
                    for port in [8001, 8000]:
                        try:
                            r = requests.get(f'http://127.0.0.1:{port}/api/dataset/mtsamples/{rec_id}', timeout=3)
                            if r.ok:
                                data = r.json()
                                st.session_state['mtsample_data'] = data
                                default_txt = data.get('transcription', '')
                                break
                        except Exception:
                            continue
                except Exception as e:
                    st.error(f"Error loading record: {e}")
        with col2:
            st.caption("Quick Select: Record 3552 (Endoscopy - 3) | Record 3739 (Consult - Jaw Pain)")
            if 'mtsample_data' in st.session_state and st.session_state['mtsample_data'].get('id') == rec_id:
                d = st.session_state['mtsample_data']
                st.success(f"**{d.get('sample_name')}** — *{d.get('medical_specialty')}* ({d.get('word_count')} words)")
                default_txt = d.get('transcription', '')

    elif input_mode == 'Upload Document (.txt, .pdf, .docx)':
        st.subheader('Upload Clinical Note / Prescription')
        uploaded_file = st.file_uploader('Choose a file', type=['txt', 'pdf', 'docx'])
        if uploaded_file is not None:
            try:
                files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                for port in [8001, 8000]:
                    try:
                        r = requests.post(f'http://127.0.0.1:{port}/api/upload', files=files, timeout=5)
                        if r.ok:
                            up_data = r.json()
                            st.success(f"Extracted from **{up_data.get('filename')}** ({up_data.get('file_type')}): {up_data.get('word_count')} words")
                            default_txt = up_data.get('text', '')
                            break
                    except Exception:
                        continue
            except Exception as e:
                st.error(f"Error uploading file: {e}")

    txt = st.text_area('Clinical Note Narrative', value=default_txt or st.session_state.get('note_text', ''), height=200)

    if st.button('Analyze Note') and txt:
        try:
            st.session_state['note_text'] = txt
            payload = {'patient_id': 1, 'document_id': 1, 'text': txt}
            response = None
            for port in [8001, 8000]:
                try:
                    response = requests.post(f'http://127.0.0.1:{port}/api/analyze', json=payload, timeout=30)
                    if response.ok:
                        break
                except Exception:
                    continue
            if response and response.ok:
                st.session_state['result'] = response.json()
                st.subheader('Analysis Result')
                st.json(st.session_state['result'])
            else:
                st.error(f'API request failed: {response.status_code if response else "Server unreachable"}')
        except Exception as e:
            st.error(f'API request failed: {e}')
elif page == 'Entity Extraction':
    if 'result' in st.session_state:
        st.subheader('Extracted Entities')
        for ent in st.session_state['result']['entities']:
            st.write(f"- **{ent['entity_type']}**: {ent['entity_text']} (source: {ent['source']})")
    else:
        st.info('Run analysis first.')
elif page == 'Guideline Matching':
    if 'result' in st.session_state:
        st.subheader('Matched Guidelines')
        for rule_id in st.session_state['result']['explanation']['matched_rules']:
            st.write(f"- Rule ID: {rule_id}")
    else:
        st.info('Run analysis first.')
elif page == 'Gap Detection':
    if 'result' in st.session_state:
        st.subheader('Detected Gaps')
        for gap in st.session_state['result']['gaps']:
            st.write(f"- **{gap['gap_type']}**: {gap['description']}")
        st.metric('Guideline Match Confidence', f"{st.session_state['result']['confidence']} %")
    else:
        st.info('Run analysis first.')
elif page == 'Timeline':
    st.subheader('Clinical Timeline & Event Sequence')

    result = st.session_state.get('result')
    entities = result.get('entities', []) if result else []
    note_text = st.session_state.get('note_text', '')

    if not result or not entities:
        st.info('No timeline data available. The current document does not contain enough clinical or temporal information to construct a timeline. Please upload/paste a clinical note and click Analyze on the Clinical Input page.')
    else:
        import re

        # Sort entities by order of appearance in the original clinical note
        def get_pos(ent):
            if not note_text:
                return 0
            pos = note_text.lower().find(ent.get('entity_text', '').lower())
            return pos if pos >= 0 else 999999

        ordered_entities = sorted(entities, key=get_pos)

        # Check for explicit calendar dates in the document text
        date_pattern = re.compile(
            r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:, \d{4})?)\b',
            re.IGNORECASE
        )
        dates_found = date_pattern.findall(note_text) if note_text else []

        if dates_found:
            st.caption(f"📅 Explicit document dates identified: {', '.join(dates_found)}")
        else:
            st.caption("ℹ️ No explicit calendar dates detected in this clinical note. Events are presented in sequence of clinical documentation (order of appearance).")

        st.markdown("### Document Event Progression")

        for idx, ent in enumerate(ordered_entities, 1):
            text_val = ent.get('entity_text', '')
            etype = ent.get('entity_type', '').upper()
            is_neg = ent.get('negated', False)

            if etype == 'INVESTIGATION':
                if is_neg:
                    st.error(f"**Step {idx} — Investigation:** {text_val} — **Not performed**")
                else:
                    st.success(f"**Step {idx} — Investigation:** {text_val} — **Performed / Present**")
            elif etype in ('DISEASE', 'CONDITION'):
                status = "Not present" if is_neg else "Active / Documented"
                st.info(f"**Step {idx} — Disease / Condition:** {text_val} ({status})")
            elif etype == 'MEDICATION':
                st.warning(f"**Step {idx} — Medication:** {text_val}")
            elif etype == 'DOSAGE':
                st.write(f"**Step {idx} — Dosage:** {text_val}")
            elif etype == 'FREQUENCY':
                st.write(f"**Step {idx} — Frequency:** {text_val}")
            else:
                status = "Not present" if is_neg else "Documented"
                st.write(f"**Step {idx} — {etype.capitalize()}:** {text_val} ({status})")

        st.markdown("---")
        st.subheader("Clinical Summary by Category")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🩺 Conditions & Investigations")
            diseases = [e['entity_text'] for e in ordered_entities if e.get('entity_type') in ('DISEASE', 'CONDITION')]
            if diseases:
                for d in dict.fromkeys(diseases):
                    st.write(f"- **Condition:** {d}")
            else:
                st.write("No conditions extracted.")

            investigations = [e for e in ordered_entities if e.get('entity_type') == 'INVESTIGATION']
            if investigations:
                for inv in investigations:
                    inv_name = inv.get('entity_text', '')
                    if inv.get('negated', False):
                        st.write(f"- **Investigation:** {inv_name} — :red[**Not performed**]")
                    else:
                        st.write(f"- **Investigation:** {inv_name} — :green[**Performed**]")
            else:
                st.write("No investigations extracted.")

        with col2:
            st.markdown("#### 💊 Medications & Dosing Regimen")
            meds = [e['entity_text'] for e in ordered_entities if e.get('entity_type') == 'MEDICATION']
            dosages = [e['entity_text'] for e in ordered_entities if e.get('entity_type') == 'DOSAGE']
            freqs = [e['entity_text'] for e in ordered_entities if e.get('entity_type') == 'FREQUENCY']

            if meds:
                for med in dict.fromkeys(meds):
                    med_dosage = dosages[0] if dosages else "Not specified"
                    med_freq = freqs[0] if freqs else "Not specified"
                    st.write(f"- **Medication:** {med}")
                    st.write(f"  - **Dosage:** {med_dosage}")
                    st.write(f"  - **Frequency:** {med_freq}")
            else:
                st.write("No medications extracted.")

# Footer disclaimer
st.caption('This prototype is for academic demonstration only and must not be used for real clinical decision‑making.')
