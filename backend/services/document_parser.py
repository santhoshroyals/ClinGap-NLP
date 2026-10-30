"""
document_parser.py - Multi-format clinical document text extractor.
Extracts text from .txt, .pdf, and .docx files without external runtime binaries.
"""

import io
import os
import zipfile
import xml.etree.ElementTree as ET
from typing import Tuple


def extract_text_from_txt(content: bytes) -> str:
    """Extracts text from raw bytes of a plain text file."""
    for enc in ('utf-8', 'latin-1', 'cp1252', 'ascii'):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    return content.decode('utf-8', errors='replace')


def extract_text_from_pdf(content: bytes) -> str:
    """Extracts text from PDF bytes using PyMuPDF (fitz) with pypdf fallback."""
    # 1. Try PyMuPDF (fast, accurate)
    try:
        import fitz
        doc = fitz.open(stream=content, filetype='pdf')
        pages = [page.get_text() for page in doc]
        text = "\n".join(p.strip() for p in pages if p.strip())
        if text.strip():
            return text
    except Exception:
        pass

    # 2. Fallback to pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or '' for page in reader.pages]
        text = "\n".join(p.strip() for p in pages if p.strip())
        if text.strip():
            return text
    except Exception as exc:
        raise ValueError(f"Failed to extract text from PDF: {exc}")

    return text.strip()


def extract_text_from_docx(content: bytes) -> str:
    """
    Extracts text from DOCX bytes using standard library zipfile + xml.etree.
    Includes regex fallback for maximum resilience against malformed XML entities.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            xml_bytes = z.read('word/document.xml')
            try:
                tree = ET.fromstring(xml_bytes)
                paragraphs = []
                # Match word processing paragraph element <w:p>
                for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    texts = [
                        node.text
                        for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
                        if node.text
                    ]
                    if texts:
                        paragraphs.append(''.join(texts))
                if paragraphs:
                    return '\n'.join(paragraphs)
            except Exception:
                pass

            # Robust fallback using regex on <w:t> nodes
            import re
            raw_xml = xml_bytes.decode('utf-8', errors='ignore')
            # Extract paragraphs
            p_matches = re.findall(r'<w:p[ >](.*?)</w:p>', raw_xml, re.DOTALL)
            paras = []
            for p_content in p_matches:
                t_matches = re.findall(r'<w:t[ >](.*?)</w:t>', p_content, re.DOTALL)
                if t_matches:
                    p_text = ''.join(t_matches).strip()
                    # Unescape common XML entities
                    p_text = p_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&apos;', "'")
                    if p_text:
                        paras.append(p_text)
            if paras:
                return '\n'.join(paras)

            # Direct fallback for all <w:t> tags
            t_all = re.findall(r'<w:t[ >](.*?)</w:t>', raw_xml, re.DOTALL)
            if t_all:
                return ' '.join(t_all)

            raise ValueError("No text nodes found in DOCX document.")
    except Exception as exc:
        raise ValueError(f"Failed to extract text from DOCX: {exc}")



def parse_document(filename: str, content: bytes) -> Tuple[str, str]:
    """
    Parses document bytes according to file extension.
    Returns (extracted_text, detected_format).
    """
    ext = os.path.splitext(filename.lower())[1]

    if ext == '.txt':
        text = extract_text_from_txt(content)
        fmt = 'TXT'
    elif ext == '.pdf':
        text = extract_text_from_pdf(content)
        fmt = 'PDF'
    elif ext in ('.docx', '.doc'):
        text = extract_text_from_docx(content)
        fmt = 'DOCX'
    else:
        raise ValueError(f"Unsupported document format '{ext}'. Allowed: .txt, .pdf, .docx")

    cleaned = text.strip()
    if not cleaned:
        raise ValueError(f"No extractable text was found in the uploaded {fmt} document.")

    return cleaned, fmt
