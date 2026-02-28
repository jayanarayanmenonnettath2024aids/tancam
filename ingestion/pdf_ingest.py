import pdfplumber


def extract_pdf_text_and_tables(file_path):
    extracted_text = ""
    extracted_tables = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            # Extract plain text
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"

            # Extract tables
            tables = page.extract_tables()
            for table in tables:
                extracted_tables.append(table)

    return extracted_text, extracted_tables