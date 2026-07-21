import os
import re
import string
import PyPDF2
import docx
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import spacy

# Try loading spacy model, fallback to a simple approach if not downloaded
try:
    nlp = spacy.load('en_core_web_sm')
except:
    import subprocess
    import sys
    subprocess.call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'])
    nlp = spacy.load('en_core_web_sm')

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class AdvancedResumeAnalyzer:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        # Extensive skill dictionary for extraction
        self.skills_db = [
            'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'html', 'css', 
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
            'spring boot', 'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
            'machine learning', 'deep learning', 'nlp', 'computer vision', 
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'ci/cd',
            'git', 'linux', 'agile', 'scrum', 'data analysis', 'statistics'
        ]
        
        # Predefined question banks mapped to skills
        self.question_bank = {
            'python': ["What are decorators in Python?", "Explain the difference between list and tuple."],
            'machine learning': ["Explain the bias-variance tradeoff.", "How does Random Forest work?"],
            'react': ["What is the virtual DOM?", "Explain React Hooks."],
            'sql': ["What is a JOIN?", "Explain the difference between clustered and non-clustered indexes."],
            'docker': ["What is a Docker container?", "How is Docker different from virtual machines?"]
        }

    def extract_text_from_pdf(self, file_path):
        """Extracts text from a PDF file."""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in range(len(reader.pages)):
                    text += reader.pages[page].extract_text()
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return text

    def extract_text_from_docx(self, file_path):
        """Extracts text from a DOCX file."""
        text = ""
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print(f"Error reading DOCX: {e}")
        return text
        
    def extract_text(self, file_path):
        """Wrapper to extract text based on file extension."""
        if file_path.lower().endswith('.pdf'):
            return self.extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            return self.extract_text_from_docx(file_path)
        return ""

    def preprocess_text(self, text):
        """Cleans and preprocesses text (tokenization, stopwords, punctuation)."""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Tokenization
        tokens = word_tokenize(text)
        # Remove stopwords and non-alphabetic tokens
        cleaned_tokens = [word for word in tokens if word.isalpha() and word not in self.stop_words]
        return " ".join(cleaned_tokens)

    def extract_skills(self, text):
        """Extracts skills using NLTK/spaCy and string matching."""
        cleaned_text = self.preprocess_text(text)
        doc = nlp(text.lower())
        
        extracted_skills = set()
        
        # 1. Match against known skills DB
        for skill in self.skills_db:
            if re.search(r'\b' + re.escape(skill) + r'\b', cleaned_text):
                extracted_skills.add(skill)
                
        # 2. Use spaCy NER to find additional potential entities (like proper nouns)
        # (Often skills are tagged as ORG, PRODUCT, or simply NOUNs)
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT', 'GPE']:
                if ent.text.lower() in self.skills_db:
                    extracted_skills.add(ent.text.lower())
                    
        return list(extracted_skills)

    def calculate_ats_score(self, resume_skills, required_skills):
        """Predicts ATS score based on matched skills proportion."""
        if not required_skills:
            return 0, []
            
        resume_skills_set = set(resume_skills)
        required_skills_set = set(required_skills)
        
        matched_skills = resume_skills_set.intersection(required_skills_set)
        missing_skills = required_skills_set.difference(resume_skills_set)
        
        # Basic formula: percentage of required skills matched
        score = (len(matched_skills) / len(required_skills_set)) * 100
        
        # Give some baseline points for having skills in general (to be realistic)
        base_bonus = min(len(resume_skills) * 2, 20)
        final_score = min(score + base_bonus, 100)
        
        return round(final_score), list(missing_skills)

    def recommend_jobs(self, resume_text, jobs_df):
        """
        Recommends top 5 matching jobs using TF-IDF and Cosine Similarity.
        jobs_df should be a DataFrame with columns: ['id', 'title', 'description', 'required_skills']
        """
        cleaned_resume = self.preprocess_text(resume_text)
        
        # Preprocess job descriptions
        jobs_df['processed_desc'] = jobs_df['description'].apply(self.preprocess_text)
        
        # Vectorization
        vectorizer = TfidfVectorizer(max_features=1000)
        
        # Fit transform on all job descriptions + the resume
        all_texts = [cleaned_resume] + jobs_df['processed_desc'].tolist()
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # Calculate cosine similarity (Resume is index 0)
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        
        # Add similarities to dataframe
        jobs_df['similarity_score'] = cosine_sim
        
        # Get top 5 matches
        top_jobs = jobs_df.sort_values(by='similarity_score', ascending=False).head(5)
        
        recommendations = []
        for _, row in top_jobs.iterrows():
            recommendations.append({
                'id': row['id'],
                'title': row['title'],
                'match_percentage': round(row['similarity_score'] * 100),
                'required_skills': row['required_skills']
            })
            
        return recommendations

    def generate_interview_questions(self, skills):
        """Generates interview questions based on extracted skills."""
        questions = []
        for skill in skills:
            if skill in self.question_bank:
                questions.extend(self.question_bank[skill])
        
        # Fallback if no specific questions are mapped
        if not questions and skills:
            questions.append(f"Can you describe a project where you heavily utilized {skills[0].title()}?")
            
        # Return up to 5 unique questions
        return list(set(questions))[:5]

if __name__ == "__main__":
    # Small test when running file directly
    analyzer = AdvancedResumeAnalyzer()
    sample_text = "Experienced software engineer with deep knowledge in Python, Machine Learning, and SQL. Built APIs using Flask and deployed to AWS."
    
    print("--- NLP Resume Analysis Test ---")
    skills = analyzer.extract_skills(sample_text)
    print(f"Extracted Skills: {skills}")
    
    questions = analyzer.generate_interview_questions(skills)
    print(f"\nGenerated Interview Questions:\n" + "\n".join(questions))
