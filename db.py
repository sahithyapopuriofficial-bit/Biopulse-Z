"""
BioPulse-Z Database & Persistence Layer
Manages Patient Master Records, Cryptographic Audit Ledger, and Clinician Directory.
"""
import sqlite3
import hashlib
import time

DB_PATH = "biopulse.db"

INITIAL_PATIENTS = [
    ("BED-01", "MRN-849201", "James Wilson", 58, "M", "Acute Coronary Syndrome", "2026-10-16 08:30:00"),
    ("BED-02", "MRN-849202", "Elena Rostova", 64, "F", "Post-op CABG (Day 1)", "2026-10-16 11:15:00"),
    ("BED-03", "MRN-849203", "David Miller", 71, "M", "Decompensated Heart Failure", "2026-10-15 19:45:00"),
    ("BED-04", "MRN-849204", "Robert Vance", 67, "M", "Suspected Septic Shock", "2026-10-16 14:05:00"),
    ("BED-05", "MRN-849205", "Maria Garcia", 52, "F", "Severe Acute Pancreatitis", "2026-10-16 16:20:00"),
    ("BED-06", "MRN-849206", "Arthur Pendelton", 79, "M", "COPD Exacerbation / ARDS", "2026-10-15 22:10:00"),
    ("BED-07", "MRN-849207", "Amina Al-Mansoor", 45, "F", "Polytrauma / Hemorrhagic Shock", "2026-10-17 01:50:00"),
    ("BED-08", "MRN-849208", "Chen Wei", 61, "M", "Urosepsis / Acute Kidney Injury", "2026-10-16 20:30:00"),
    ("BED-09", "MRN-849209", "Sarah Jenkins", 38, "F", "Postpartum Hemorrhage", "2026-10-17 04:12:00"),
    ("BED-10", "MRN-849210", "Thomas Becker", 83, "M", "Aspiration Pneumonia", "2026-10-15 14:00:00"),
    ("BED-11", "MRN-849211", "Lucas Silva", 29, "M", "Traumatic Brain Injury (Subdural)", "2026-10-17 06:40:00"),
    ("BED-12", "MRN-849212", "Evelyn Reed", 74, "F", "Diabetic Ketoacidosis / Sepsis", "2026-10-16 23:15:00")
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        bed_id TEXT PRIMARY KEY,
        mrn TEXT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        diagnosis TEXT,
        admission_time TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        bed_id TEXT,
        mrn TEXT,
        action_type TEXT,
        risk_score REAL,
        shock_index REAL,
        sbar_summary TEXT,
        crypto_signature TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinicians (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        npi_license TEXT UNIQUE,
        email TEXT UNIQUE,
        password_hash TEXT,
        full_name TEXT,
        department TEXT,
        role TEXT,
        created_at TEXT
    )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM patients")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO patients (bed_id, mrn, name, age, gender, diagnosis, admission_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, INITIAL_PATIENTS)

    cursor.execute("SELECT id FROM clinicians WHERE email = 'sarah.chen@biopulse.ibm.com'")
    if not cursor.fetchone():
        salt = "z16_secure_enclave_"
        default_pwd_hash = hashlib.sha256((salt + "IBMz16Telum!").encode()).hexdigest()
        cursor.execute("""
        INSERT INTO clinicians (npi_license, email, password_hash, full_name, department, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "NPI-9482019482", 
            "sarah.chen@biopulse.ibm.com", 
            default_pwd_hash, 
            "Dr. Sarah Chen, MD", 
            "Critical Care / Trauma ICU", 
            "Attending Intensivist",
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        ))

    conn.commit()
    conn.close()

def get_all_patients():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT bed_id, mrn, name, age, gender, diagnosis, admission_time FROM patients")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "bed_id": r[0],
            "mrn": r[1],
            "name": r[2],
            "age": r[3],
            "gender": r[4],
            "diagnosis": r[5],
            "admission_time": r[6]
        }
        for r in rows
    ]

def get_patient(bed_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT bed_id, mrn, name, age, gender, diagnosis, admission_time FROM patients WHERE bed_id = ?", (bed_id,))
    r = cursor.fetchone()
    conn.close()
    if r:
        return {
            "bed_id": r[0],
            "mrn": r[1],
            "name": r[2],
            "age": r[3],
            "gender": r[4],
            "diagnosis": r[5],
            "admission_time": r[6]
        }
    return None

def record_audit_action(bed_id, mrn, action_type, risk_score, shock_index, sbar_summary):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    utc_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sig_raw = f"{bed_id}|{mrn}|{action_type}|{risk_score}|{shock_index}|{utc_time}"
    crypto_sig = "zERT-MLDSA-" + hashlib.sha256(sig_raw.encode()).hexdigest()[:24].upper()
    
    cursor.execute("""
    INSERT INTO audit_logs (timestamp, bed_id, mrn, action_type, risk_score, shock_index, sbar_summary, crypto_signature)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (utc_time, bed_id, mrn, action_type, risk_score, shock_index, sbar_summary, crypto_sig))
    
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id

def hash_password(password: str) -> str:
    salt = "z16_secure_enclave_"
    return hashlib.sha256((salt + password).encode()).hexdigest()

def register_clinician(npi_license: str, email: str, password: str, full_name: str, department: str, role: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        pwd_hash = hash_password(password)
        cursor.execute("""
        INSERT INTO clinicians (npi_license, email, password_hash, full_name, department, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (npi_license, email, pwd_hash, full_name, department, role, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
        conn.commit()
        return True, "Registration successful"
    except sqlite3.IntegrityError:
        return False, "NPI License or Email already registered in hospital directory"
    finally:
        conn.close()

def authenticate_clinician(identifier: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    cursor.execute("""
    SELECT npi_license, email, full_name, department, role FROM clinicians
    WHERE (email = ? OR npi_license = ?) AND password_hash = ?
    """, (identifier, identifier, pwd_hash))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            "npi_license": user[0],
            "email": user[1],
            "full_name": user[2],
            "department": user[3],
            "role": user[4]
        }
    return None