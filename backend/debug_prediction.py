from ml.predictor import predictor
import sys

# Symptoms reported by user
user_symptoms = ["itching", "burning urination", "cold"]

print(f"Testing prediction for: {user_symptoms}")

# 1. Check symptom validation/mapping
print("\n--- Symptom Validation ---")
mapped_symptoms = []
for s in user_symptoms:
    match, score = predictor.check_symptom(s)
    print(f"Input: '{s}' -> Match: '{match}' (Score: {score})")
    if score > 70:
        mapped_symptoms.append(match)
    else:
        print(f"  [WARNING] '{s}' did not match closely enough.")

print(f"\nMapped Symptoms for Prediction: {mapped_symptoms}")

# 2. Predict
print("\n--- Prediction ---")
if len(mapped_symptoms) == 3:
    try:
        result = predictor.predict(mapped_symptoms)
        print(f"Result: {str(result).encode('utf-8')}")
    except Exception as e:
        print(f"Prediction Error: {e}")
else:
    print("Not enough valid symptoms to predict (logic check).")
