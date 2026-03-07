import pdfplumber
import pytesseract
from PIL import Image
import fitz
import os

if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_pdf_text_and_tables(file_path):
    extracted_text = ""
    extracted_tables = []

    # Try pdfplumber first
    with pdfplumber.open(file_path) as pdf:
        extracted_text = ' '.join([p.extract_text() or '' for p in pdf.pages])
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                extracted_tables.append(table)
                
    # If empty, fall back to OCR
    if len(extracted_text.strip()) < 50:
        try:
            doc = fitz.open(file_path)
            extracted_text = ''
            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                extracted_text += pytesseract.image_to_string(img)
        except Exception as e:
            print(f"OCR Fail: {e}")
            pass

    return extracted_text, extracted_tables