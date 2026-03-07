import pandas as pd
import glob
import os

def ingest_excel(file_path):
    df = pd.read_excel(file_path)
    records = df.to_dict(orient="records")
    return records
    
def ingest_excel_folder(folder_path):
    all_records = []
    files = glob.glob(os.path.join(folder_path, '*.xlsx'))
    files += glob.glob(os.path.join(folder_path, '*.csv'))
    for f in files:
        records = ingest_excel(f)
        all_records.extend(records)
    return all_records