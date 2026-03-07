import os
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from db.models import Shipment, AnomalyRecord
import datetime

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'anomaly_model.pkl')

def train_or_load_model(df):
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    # We always retrain here for simplicity if the df has new data, 
    # but could cache it.
    model = IsolationForest(contamination=0.05, random_state=42)
    # Features: quantity, unit_value, total_value
    features = df[['quantity', 'unit_value', 'total_value']].fillna(0)
    
    if len(features) > 10:
        model.fit(features)
        joblib.dump(model, MODEL_PATH)
        return model
    return None

def detect_anomalies_in_db(db_session):
    # Fetch all shipments
    shipments = db_session.query(Shipment).all()
    if not shipments:
        return 0, 0
        
    data = []
    for s in shipments:
        data.append({
            'id': s.id,
            'quantity': s.quantity or 0,
            'unit_value': s.unit_value or 0,
            'total_value': s.total_value or 0,
        })
        
    df = pd.DataFrame(data)
    
    model = train_or_load_model(df)
    if not model:
        return len(df), 0 # Not enough data
        
    features = df[['quantity', 'unit_value', 'total_value']]
    df['anomaly_score'] = model.decision_function(features)
    # Convert score to an intuitive 0-1 scale where 1 is highly anomalous
    # decision_function returns negative for anomalies.
    # Let's normalize it to 0-1
    min_score = df['anomaly_score'].min()
    max_score = df['anomaly_score'].max()
    
    if max_score != min_score:
        # Invert it so higher means more anomalous
        df['anomaly_prob'] = 1 - ((df['anomaly_score'] - min_score) / (max_score - min_score))
    else:
        df['anomaly_prob'] = 0.0
        
    df['is_anomaly'] = model.predict(features) == -1
    
    anomalies_found = 0
    now = datetime.datetime.utcnow()
    
    for _, row in df.iterrows():
        # Update or create record
        record = db_session.query(AnomalyRecord).filter(
            AnomalyRecord.record_type == 'shipment',
            AnomalyRecord.record_id == row['id']
        ).first()
        
        if not record:
            record = AnomalyRecord(
                record_type='shipment',
                record_id=row['id']
            )
            db_session.add(record)
            
        record.anomaly_score = float(row['anomaly_prob'])
        record.is_anomaly = bool(row['is_anomaly'])
        
        if record.is_anomaly:
            anomalies_found += 1
            record.description = f"Suspicious transaction values detected (value: {row['total_value']})"
        else:
            record.description = "Normal transaction"
            
        record.feature_values = {
            "quantity": float(row['quantity']),
            "unit_value": float(row['unit_value']),
            "total_value": float(row['total_value'])
        }
        record.detected_at = now
        
    db_session.commit()
    return len(df), anomalies_found
