import joblib
import os
import numpy as np
import pandas as pd
from fuzzywuzzy import process
from deep_translator import GoogleTranslator

class DiseasePredictor:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.model = None
        self.all_symptoms = None
        self.disease_info = None
        self.precautions = None
        self.severity = None
        self.symptom_aliases = None
        self.load_artifacts()

    def load_artifacts(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found at {self.model_path}")
            
        artifacts = joblib.load(self.model_path)
        self.model = artifacts['model']
        # Load all models if available
        self.all_models = artifacts.get('all_models', {})
        self.all_symptoms = artifacts['all_symptoms']
        
        # Load other CSVs
        try:
            self.disease_info = pd.read_csv(os.path.join(self.data_dir, 'disease_info.csv')).set_index('disease')
            self.precautions = pd.read_csv(os.path.join(self.data_dir, 'disease_precautions.csv'))
            self.severity = pd.read_csv(os.path.join(self.data_dir, 'disease_severity.csv')).set_index('disease')
        except Exception as e:
            print(f"Error loading CSVs: {e}")

        try:
            self.symptom_aliases = pd.read_csv(os.path.join(self.data_dir, 'symptom_aliases.csv'))
        except FileNotFoundError:
            self.symptom_aliases = None

    def check_symptom(self, user_input, lang='en'):
        if not user_input or self.all_symptoms is None:
            return None, 0
        text_to_check = user_input
        if lang != 'en':
            try:
                translator = GoogleTranslator(source='auto', target='en')
                translated = translator.translate(user_input)
                text_to_check = translated
            except Exception as e:
                print(f"Translation error: {e}")
        match, score = process.extractOne(text_to_check, self.all_symptoms)
        return match, score

    def predict(self, symptoms_list):
        if self.all_symptoms is None:
            return None

        # Create feature vector
        vector = [0] * len(self.all_symptoms)
        try:
            symptom_to_index = {str(s).lower().strip(): i for i, s in enumerate(self.all_symptoms)}
        except Exception as e:
            print(f"Index creation error: {e}")
            symptom_to_index = {}
        
        matched_symptoms = []
        for s in symptoms_list:
            s_clean = str(s).lower().strip()
            if s_clean in symptom_to_index:
                idx = symptom_to_index[s_clean]
                vector[idx] = 1
                matched_symptoms.append(s_clean)
            else:
                print(f"Warning: Symptom '{s}' validated but not found in index.")
                
        if not matched_symptoms:
            return None
            
        # Comparison logic
        comparison = []
        best_result = None
        best_score = -1 # Score = Confidence - Penalty
        
        # Use all available models
        models_to_run = self.all_models if self.all_models else {'Default': self.model}
        
        for name, model in models_to_run.items():
            try:
                pred = model.predict([vector])[0]
                conf = 0.0
                if hasattr(model, 'predict_proba'):
                    p = model.predict_proba([vector])[0]
                    conf = float(max(p)) * 100
                else:
                    conf = 100.0 if pred else 0.0
                
                # Report raw confidence in comparison
                comparison.append({
                    'model': name,
                    'disease': pred,
                    'confidence': conf
                })
                
                # Calculate selection score
                # Penalty for Decision Tree to avoid overfitting dominance
                penalty = 0
                if 'Decision Tree' in name or 'DecisionTree' in name:
                    penalty = 5.0 # Penalize DT by 5% to prefer ensemble methods
                elif 'Naive Bayes' in name:
                    penalty = 2.0 # Slightly penalize NB
                
                score = conf - penalty
                
                # Check if this is the best result so far
                if score > best_score:
                    best_score = score
                    best_result = {
                        'disease': pred,
                        'confidence': conf, # Return actual confidence
                        'model_used': name 
                    }
            except Exception as ex:
                print(f"Error predicting with {name}: {ex}")
                
        # Sort comparison by confidence descending
        comparison.sort(key=lambda x: x['confidence'], reverse=True)
        
        # If no valid results found
        if not best_result:
            return None

        # Format response using the best result
        return self.format_response(
            best_result['disease'], 
            best_result['confidence'], 
            matched_symptoms, 
            comparison
        )

    def format_response(self, disease, confidence, matched_symptoms, comparison=None):
        # Fetch details
        desc = {}
        if self.disease_info is not None and disease in self.disease_info.index:
            desc = self.disease_info.loc[disease]
            
        sev = 'Medium'
        if self.severity is not None and disease in self.severity.index:
            sev = self.severity.loc[disease]['severity']
        
        # Get precautions
        precaution_list = []
        if self.precautions is not None:
            prec_rows = self.precautions[self.precautions['disease'] == disease]
            if not prec_rows.empty:
                for index, row in prec_rows.head(3).iterrows():
                    p = {
                        'en': row.get('precaution_en', 'Consult a doctor'),
                        'hi': row.get('precaution_hi', 'डॉक्टर से सलाह लें'),
                        'ta': row.get('precaution_ta', 'மருத்துவரை அணுகவும்')
                    }
                    precaution_list.append(p)

        return {
            'disease': disease,
            'confidence': confidence,
            'severity': sev,
            'description': {
                'en': desc.get('description_en', '') if hasattr(desc, 'get') else '',
                'hi': desc.get('description_hi', '') if hasattr(desc, 'get') else '',
                'ta': desc.get('description_ta', '') if hasattr(desc, 'get') else ''
            },
            'precautions': precaution_list,
            'matched_symptoms': matched_symptoms,
            'comparison': comparison or []
        }

# Global instance
predictor = DiseasePredictor()
