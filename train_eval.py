import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import os

from ml_engine import AdvancedResumeAnalyzer

def create_sample_dataset():
    """Generates a large sample CSV dataset of resumes for high accuracy training."""
    print("Generating large sample dataset...")
    import random
    
    categories = {
        "Data Science & AI": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "NLP", "Pandas", "Numpy", "Data Analysis", "SQL", "Statistics", "Computer Vision", "Scikit-Learn"],
        "Frontend Engineering": ["HTML", "CSS", "JavaScript", "React", "Vue", "Angular", "TypeScript", "UI/UX", "Tailwind", "Bootstrap", "Web Design", "Responsive Design", "Figma"],
        "Backend Engineering": ["Java", "Spring Boot", "Python", "Django", "Flask", "Node.js", "Express", "SQL", "MySQL", "PostgreSQL", "MongoDB", "REST APIs", "Microservices", "Redis"]
    }
    
    data = {'resume_text': [], 'job_category': []}
    
    # Generate 150 resumes (50 per category)
    for category, skills in categories.items():
        for i in range(50):
            # Pick 5-8 random skills for this resume
            num_skills = random.randint(5, 8)
            selected_skills = random.sample(skills, num_skills)
            
            # Create a synthetic resume sentence
            templates = [
                f"Experienced software engineer proficient in {', '.join(selected_skills)}.",
                f"Strong background using {', '.join(selected_skills)} for scalable applications.",
                f"Expert in {', '.join(selected_skills)} with a proven track record.",
                f"Developed multiple projects utilizing {', '.join(selected_skills)}."
            ]
            
            resume = random.choice(templates)
            # Occasionally inject noise
            if random.random() > 0.8:
                resume += " Also familiar with Agile and Git."
                
            data['resume_text'].append(resume)
            data['job_category'].append(category)
            
    df = pd.DataFrame(data)
    # Shuffle dataset
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    df.to_csv('sample_resumes.csv', index=False)
    print("Dataset saved as 'sample_resumes.csv' with 150 records.")
    return df

def train_and_evaluate():
    """Trains a classifier and evaluates its accuracy and confusion matrix."""
    print("\n--- Training and Evaluation ---")
    
    # 1. Load Data
    if not os.path.exists('sample_resumes.csv'):
        df = create_sample_dataset()
    else:
        df = pd.read_csv('sample_resumes.csv')
        
    analyzer = AdvancedResumeAnalyzer()
    
    # 2. Preprocess Text
    print("Preprocessing text using NLP...")
    df['cleaned_text'] = df['resume_text'].apply(analyzer.preprocess_text)
    
    # 3. Vectorization (TF-IDF)
    print("Vectorizing data using TF-IDF...")
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df['cleaned_text'])
    y = df['job_category']
    
    # 4. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    # 5. Model Training
    print("Training RandomForest Classifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # 6. Evaluation
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {accuracy * 100:.2f}%")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    
    # 7. Confusion Matrix
    print("\nConfusion Matrix:")
    categories = model.classes_
    cm = confusion_matrix(y_test, y_pred, labels=categories)
    
    cm_df = pd.DataFrame(cm, index=categories, columns=categories)
    print(cm_df)
    
    # Optional: Generate a text-based visual representation of confusion matrix
    print("\nConfusion Matrix Interpretation:")
    for i, true_cat in enumerate(categories):
        for j, pred_cat in enumerate(categories):
            if cm[i, j] > 0:
                if i == j:
                    print(f"- Correctly predicted {cm[i,j]} instances of '{true_cat}'")
                else:
                    print(f"- Incorrectly predicted '{true_cat}' as '{pred_cat}' ({cm[i,j]} instances)")

if __name__ == "__main__":
    # Create the dataset
    create_sample_dataset()
    # Train and evaluate the ML module
    train_and_evaluate()
