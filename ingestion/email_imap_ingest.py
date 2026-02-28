import imaplib
import email
import os
import re
from email.header import decode_header

DOWNLOAD_FOLDER = "data/email_pdfs"


def extract_invoice_from_text(text):
    invoice = {}

    invoice_no = re.search(r"Invoice\s*No[:\-]?\s*(\S+)", text, re.IGNORECASE)
    client = re.search(r"Client[:\-]?\s*(.+)", text, re.IGNORECASE)
    gst = re.search(r"GST[:\-]?\s*(\S+)", text, re.IGNORECASE)
    amount = re.search(r"Amount[:\-]?\s*(\d+)", text, re.IGNORECASE)
    date = re.search(r"Date[:\-]?\s*([\d\-\/]+)", text, re.IGNORECASE)

    if invoice_no:
        invoice["invoice_no"] = invoice_no.group(1)
    if client:
        invoice["client_name"] = client.group(1).strip()
    if gst:
        invoice["gst_id"] = gst.group(1)
    if amount:
        invoice["amount"] = amount.group(1)
    if date:
        invoice["date"] = date.group(1)

    return invoice


def ingest_unseen_emails(username, app_password):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, app_password)
    mail.select("inbox")

    status, messages = mail.search(None, "UNSEEN")

    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

    extracted_invoices = []

    for num in messages[0].split():
        status, msg_data = mail.fetch(num, "(RFC822)")

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")

                body = ""
                has_invoice_keyword = False

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        # Extract body
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")

                        # Download PDF attachments
                        if "attachment" in content_disposition:
                            filename = part.get_filename()
                            if filename and filename.endswith(".pdf"):
                                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                                with open(filepath, "wb") as f:
                                    f.write(part.get_payload(decode=True))
                                print(f"Saved PDF: {filepath}")

                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                # Ignore marketing emails
                if "invoice" not in subject.lower() and "invoice" not in body.lower():
                    continue

                # Extract invoice data from body
                invoice_data = extract_invoice_from_text(body)

                if invoice_data:
                    extracted_invoices.append(invoice_data)
                    print("Extracted Invoice:", invoice_data)

    mail.logout()
    return extracted_invoices