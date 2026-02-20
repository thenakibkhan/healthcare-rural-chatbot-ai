import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pkl')

def load_data():
    """Validates and loads dataset files."""
    required_files = ['disease_symptoms.csv', 'disease_info.csv']
    for f in required_files:
        if not os.path.exists(os.path.join(DATA_DIR, f)):
            raise FileNotFoundError(f"Missing required file: {f}")
            
    # Load symptoms mapping
    df_symptoms = pd.read_csv(os.path.join(DATA_DIR, 'disease_symptoms.csv'))
    # Load disease list to ensure we have all classes
    df_info = pd.read_csv(os.path.join(DATA_DIR, 'disease_info.csv'))
    
    return df_symptoms, df_info['disease'].unique()

def preprocess_data(df_symptoms, all_diseases):
    """
    Converts symptom list into a binary feature matrix.
    Rows: Diseases (duplicated for variation or just one per disease?)
    
    The provided dataset seems to be just mappings: Disease -> Symptom.
    To train a model, we ideally need multiple samples per disease with varying symptoms.
    
    Since we only have a static mapping, we will generate synthetic samples 
    by augmenting the data (randomly dropping symptoms) to make the model robust.
    """
    
    # 1. Pivot to get one row per disease with a list of symptoms
    disease_symptom_map = df_symptoms.groupby('disease')['symptom'].apply(list).to_dict()
    
    # Get all unique symptoms
    all_symptoms = sorted(df_symptoms['symptom'].unique())
    symptom_to_index = {symptom: i for i, symptom in enumerate(all_symptoms)}
    
    X = []
    y = []
    
    # Generate synthetic data
    # Strategy: For each disease, create original sample + variations with 1-2 symptoms missing
    SAMPLES_PER_DISEASE = 50 
    
    for disease, symptoms in disease_symptom_map.items():
        # Original full symptom vector
        base_vector = [0] * len(all_symptoms)
        for s in symptoms:
            if s in symptom_to_index:
                base_vector[symptom_to_index[s]] = 1
        
        # Add the perfect case
        X.append(base_vector)
        y.append(disease)
        
        # Add variations (data augmentation)
        if len(symptoms) > 1:
            for _ in range(SAMPLES_PER_DISEASE):
                # Randomly keep 50-90% of symptoms to simulate partial reporting
                keep_prob = np.random.uniform(0.5, 0.9)
                aug_vector = [0] * len(all_symptoms)
                for s in symptoms:
                    if s in symptom_to_index and np.random.rand() < keep_prob:
                        aug_vector[symptom_to_index[s]] = 1
                
                # Only add if at least one symptom is present
                if sum(aug_vector) > 0:
                    X.append(aug_vector)
                    y.append(disease)
                    
    return np.array(X), np.array(y), all_symptoms

def train_and_evaluate(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    models = {
        "Naive Bayes": MultinomialNB(),
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Decision Tree": DecisionTreeClassifier(max_depth=10), # Limit depth to avoid 100% confidence on all leaves
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42), # Ensemble for better probabilities
        "SVM": SVC(kernel='linear', probability=True)
    }
    
    best_model = None
    best_accuracy = 0
    results = {}
    
    print(f" {'Algorithm':<20} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("-" * 75)
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        print(f"{name:<20} | {acc:.4f}     | {prec:.4f}    | {rec:.4f}    | {f1:.4f}")
        
        results[name] = {"accuracy": acc, "model": model}
        
        # Logic to prefer Random Forest if accuracy is close to best, or just pick best
        # For this specific user request, we want to ensure we don't just pick the overfitted 1.0 DT if RF is also good.
        if acc > best_accuracy:
            best_accuracy = acc
            best_model = model
            
    # Force usage of Random Forest or constrained Tree if they are good enough?
    # User asked to "Limit Tree Depth".
    # By limiting max_depth=10 above, we achieved that.
    # If the Tree is still the best, it will be saved.
    # However, Random Forest is generally better for "probabilities".
    # Let's fallback to Random Forest if Decision Tree is selected but RF is within 1% accuracy?
    # Actually, simple is better. The max_depth change alone should fix the "always 100%" issue on the Tree.
            
    print("-" * 75)
    print(f"Best Model: {best_model.__class__.__name__} with Accuracy: {best_accuracy:.4f}")
    return best_model, results

def main():
    print("Loading data...")
    df_symptoms, all_diseases = load_data()
    
    print("Preprocessing and augmenting data...")
    X, y, all_symptoms = preprocess_data(df_symptoms, all_diseases)
    print(f"Total samples generated: {len(X)}")
    print(f"Total features (symptoms): {len(all_symptoms)}")
    
    print("Training models...")
    best_model, results = train_and_evaluate(X, y)
    
    # Save model and vectorizer info
    print("Saving all models...")
    # Modified to save ALL models for comparison feature
    artifacts = {
        "model": best_model, # Keep best model as primary
        "all_models": {k: v['model'] for k, v in results.items()}, # Save all for comparison
        "all_symptoms": all_symptoms,
        "results": {k: v['accuracy'] for k, v in results.items()}
    }
    joblib.dump(artifacts, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    main()
