import pandas as pd

def ingest_excel(file_path):
    df = pd.read_excel(file_path)
    records = df.to_dict(orient="records")
    return records