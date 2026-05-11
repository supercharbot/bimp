import io

def extract_email_text(raw_email):
    body = raw_email.get('body', '')
    if raw_email.get('html'):
        import html2text
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        body = h.handle(raw_email['html'])
    return body.strip()

def extract_pdf_text(file_bytes):
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    return '\n'.join(page.extract_text() for page in reader.pages if page.extract_text())

def extract_docx_text(file_bytes):
    import docx
    doc = docx.Document(io.BytesIO(file_bytes))
    return '\n'.join(para.text for para in doc.paragraphs if para.text)

def extract_text(raw_input, file_bytes=None):
    if 'body' in raw_input or 'html' in raw_input:
        return extract_email_text(raw_input)
    file_type = raw_input.get('file_type', '').lower()
    if 'pdf' in file_type:
        return extract_pdf_text(file_bytes)
    elif 'docx' in file_type or 'word' in file_type:
        return extract_docx_text(file_bytes)
    elif file_bytes:
        return file_bytes.decode('utf-8', errors='ignore')
    return ''
