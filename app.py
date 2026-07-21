from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from ml_engine import AdvancedResumeAnalyzer
import os
import sqlite3
import hashlib

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'super_secret_key'

# Initialize DB
def init_db():
    conn = sqlite3.connect('resume_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password_hash TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

analyzer = AdvancedResumeAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth')
def auth():
    return render_template('auth.html')

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        conn = sqlite3.connect('resume_db.sqlite')
        c = conn.cursor()
        c.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", (name, email, password_hash))
        conn.commit()
        conn.close()
        session['user'] = email
        return redirect(url_for('dashboard'))
    except sqlite3.IntegrityError:
        return render_template('auth.html', error="Email already exists. Please login.")

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect('resume_db.sqlite')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password_hash=?", (email, password_hash))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['user'] = email
        return redirect(url_for('dashboard'))
    else:
        return render_template('auth.html', error="Invalid credentials. Please try again.")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/api/analyze', methods=['POST'])
def analyze_resume():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized. Please login.'}), 401
        
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    # Save the file temporarily
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    
    # Extract actual text from the file (PDF or DOCX)
    extracted_text = analyzer.extract_text(filepath)
    
    # Clean up temporary file
    try:
        os.remove(filepath)
    except Exception as e:
        print(f"Error removing temp file: {e}")
        
    if not extracted_text.strip():
        return jsonify({'error': 'Could not extract text from the document. Please ensure it is not scanned/empty.'}), 400
    
    import pandas as pd
    dummy_jobs = pd.DataFrame({
        'id': [1, 2, 3],
        'title': ['Software Engineer', 'Data Scientist', 'Frontend Developer'],
        'description': ['Looking for Python, SQL, Backend, AWS, Docker', 'Looking for Python, Machine Learning, Data Analysis, Pandas, NLP', 'Looking for HTML, CSS, React, JavaScript, Node.js'],
        'required_skills': ['python, sql, aws, docker', 'python, machine learning, pandas, sql, nlp', 'html, css, react, javascript, node.js']
    })
    
    extracted_skills = analyzer.extract_skills(extracted_text)
    
    # Dynamic required skills based on a general tech profile
    required_skills = ['python', 'machine learning', 'sql', 'docker', 'aws', 'pandas', 'nlp', 'react', 'javascript', 'html', 'css']
    
    score, missing_skills = analyzer.calculate_ats_score(extracted_skills, required_skills)
    job_recs = analyzer.recommend_jobs(extracted_text, dummy_jobs)
    
    return jsonify({
        'ats_score': score,
        'skills': [s.title() for s in extracted_skills],
        'missing_skills': [s.title() for s in missing_skills],
        'recommendations': job_recs
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)