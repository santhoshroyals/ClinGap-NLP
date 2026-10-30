import os, sqlite3, datetime

def get_db_path():
    return os.path.join(os.getcwd(), 'clinngap.db')

db_path = get_db_path()
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Insert a new patient
cur.execute('INSERT INTO patients (name) VALUES (?)', ('Demo Patient 2',))
patient_id = cur.lastrowid

# Clinical note with disease and investigation
note = """The patient has diabetes mellitus. CBC was not performed. HbA1c was performed and the result was 8.2%. The patient is taking metformin 500 mg twice daily."""
cur.execute(
    'INSERT INTO documents (patient_id, title, content, doc_type, created_at) VALUES (?,?,?,?,?)',
    (patient_id, 'Demo Diabetes Note', note, 'note', datetime.datetime.utcnow())
)

document_id = cur.lastrowid
conn.commit()
print('Inserted patient_id', patient_id, 'document_id', document_id)
conn.close()
