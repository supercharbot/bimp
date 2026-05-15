import io
import logging

logger = logging.getLogger(__name__)


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
    import pytesseract
    from PIL import Image

    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    all_parts = []

    for i, page in enumerate(reader.pages):
        parts = []

        # Text layer
        text = page.extract_text() or ''
        if text.strip():
            parts.append(text.strip())

        # Embedded images — OCR each one
        try:
            for img_key in page.images:
                img_data = img_key.data
                try:
                    img = Image.open(io.BytesIO(img_data))
                    if img.width < 100 or img.height < 100:
                        continue
                    ocr_text = pytesseract.image_to_string(img).strip()
                    if len(ocr_text.split()) >= 5:
                        parts.append(ocr_text)
                        logger.info(f"Page {i+1}: OCR extracted {len(ocr_text.split())} words from image")
                except Exception as e:
                    logger.debug(f"Page {i+1}: skipped image: {e}")
        except Exception as e:
            logger.debug(f"Page {i+1}: no images or extraction failed: {e}")

        if parts:
            all_parts.append('\n'.join(parts))

    result = '\n\n'.join(all_parts)
    logger.info(f"PDF: {len(reader.pages)} pages, {len(result.split())} total words")
    return result.strip()


def extract_docx_text(file_bytes):
    import docx
    doc = docx.Document(io.BytesIO(file_bytes))
    return '\n'.join(para.text for para in doc.paragraphs if para.text)


def extract_xlsx_text(file_bytes):
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    rows = []
    for sheet in wb.sheetnames:
        ws = wb[sheet]
        rows.append(f"--- Sheet: {sheet} ---")
        for row in ws.iter_rows(values_only=True):
            vals = [str(c) if c is not None else '' for c in row]
            if any(vals):
                rows.append('\t'.join(vals))
    wb.close()
    return '\n'.join(rows)


def extract_text(raw_input, file_bytes=None):
    if 'body' in raw_input or 'html' in raw_input:
        return extract_email_text(raw_input)

    file_type = raw_input.get('file_type', '').lower()

    if 'pdf' in file_type:
        return extract_pdf_text(file_bytes)
    elif 'docx' in file_type or 'word' in file_type:
        return extract_docx_text(file_bytes)
    elif 'spreadsheet' in file_type or 'xlsx' in file_type or 'excel' in file_type:
        return extract_xlsx_text(file_bytes)
    elif file_bytes:
        return file_bytes.decode('utf-8', errors='ignore')
    return ''
