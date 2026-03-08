import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

from transformers import pipeline

# Load a lightweight zero-shot classification model from Hugging Face
# We use typeform/distilbert-base-uncased-mnli to minimize memory footprint and maximize speed locally.
try:
    print("Loading Local LLM (Zero-Shot Classifier) into memory...")
    classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli", device=-1)
    print("Local LLM Loaded successfully.")
except Exception as e:
    print(f"Failed to load local LLM: {e}")
    classifier = None

CANDIDATE_INTENTS = [
    "TOTAL_VALUE",
    "COUNT_PENDING",
    "COUNT_SHIPMENTS",
    "TOP_N_CUSTOMERS",
    "STATUS_CHECK",
    "COMPLIANCE_ALERTS",
    "ANOMALY_CHECK",
    "DATE_FILTER",
    "GENERAL"
]

def get_intent_from_llm(query: str):
    """
    Passes the natural language query locally to the Neural Network
    to calculate zero-shot probabilities against our defined intents.
    """
    if not classifier:
        return "GENERAL", 0.0
        
    try:
        # Format candidate labels nicely for the model
        labels = [i.replace("_", " ").lower() for i in CANDIDATE_INTENTS]
        
        # Run local inference
        result = classifier(query, candidate_labels=labels)
        
        top_label = result['labels'][0]
        confidence = result['scores'][0]
        
        # Map back to enum
        intent_enum = top_label.replace(" ", "_").upper()
        
        # Safe fallback
        if intent_enum not in CANDIDATE_INTENTS:
            intent_enum = "GENERAL"
            
        print(f"LLM Classification Result: {intent_enum} ({confidence:.2f})")
        return intent_enum, confidence
        
    except Exception as e:
        print(f"LLM Inference error: {e}")
        return "GENERAL", 0.0
