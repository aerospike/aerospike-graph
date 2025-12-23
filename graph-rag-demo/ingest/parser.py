"""
Phase 2: Document parser

Supports: .txt, .md, .pdf files
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# PDF support
try:
    import fitz  # PyMuPDF
    PDF_SUPPORTED = True
except ImportError:
    PDF_SUPPORTED = False
    print("⚠️  PyMuPDF not installed. PDF support disabled.")
    print("   Install with: pip install PyMuPDF")


@dataclass
class Document:
    """Represents a parsed document"""
    id: str
    title: str
    content: str
    source: str  # file path
    
    def __repr__(self):
        preview = self.content[:100] + "..." if len(self.content) > 100 else self.content
        return f"Document(id={self.id}, title={self.title}, len={len(self.content)})"


def parse_pdf(file_path: str) -> Optional[str]:
    """
    Extract text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text or None if parsing fails
    """
    if not PDF_SUPPORTED:
        print(f"❌ PDF support not available. Install PyMuPDF.")
        return None
    
    try:
        doc = fitz.open(file_path)
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(text)
        
        doc.close()
        
        full_text = "\n\n".join(text_parts)
        return full_text if full_text.strip() else None
        
    except Exception as e:
        print(f"❌ Error parsing PDF {file_path}: {e}")
        return None


def parse_text_file(file_path: str) -> Optional[str]:
    """
    Read content from a text or markdown file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File content or None if reading fails
    """
    try:
        return Path(file_path).read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return None


def parse_file(file_path: str) -> Optional[Document]:
    """
    Parse a single file and return a Document.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Document object or None if parsing fails
    """
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    # Check supported extensions
    text_extensions = {'.txt', '.md', '.markdown'}
    pdf_extensions = {'.pdf'}
    
    suffix = path.suffix.lower()
    
    if suffix in text_extensions:
        content = parse_text_file(file_path)
    elif suffix in pdf_extensions:
        content = parse_pdf(file_path)
    else:
        supported = text_extensions | (pdf_extensions if PDF_SUPPORTED else set())
        print(f"❌ Unsupported file type: {suffix}")
        print(f"   Supported: {supported}")
        return None
    
    if not content or not content.strip():
        print(f"❌ No content extracted from: {file_path}")
        return None
    
    # Generate a simple ID from filename
    doc_id = path.stem.lower().replace(' ', '_').replace('-', '_')
    
    # Use filename as title (without extension)
    title = path.stem.replace('_', ' ').replace('-', ' ').title()
    
    return Document(
        id=doc_id,
        title=title,
        content=content,
        source=str(path.absolute())
    )


def parse_directory(dir_path: str) -> list[Document]:
    """
    Parse all supported files in a directory.
    
    Args:
        dir_path: Path to directory containing documents
        
    Returns:
        List of Document objects
    """
    path = Path(dir_path)
    
    if not path.exists():
        print(f"❌ Directory not found: {dir_path}")
        return []
    
    if not path.is_dir():
        print(f"❌ Not a directory: {dir_path}")
        return []
    
    documents = []
    text_extensions = {'.txt', '.md', '.markdown'}
    pdf_extensions = {'.pdf'} if PDF_SUPPORTED else set()
    supported_extensions = text_extensions | pdf_extensions
    
    for file_path in sorted(path.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            doc = parse_file(str(file_path))
            if doc:
                documents.append(doc)
                print(f"✅ Parsed: {file_path.name} ({len(doc.content)} chars)")
    
    print(f"\n📄 Total documents parsed: {len(documents)}")
    return documents


if __name__ == "__main__":
    # Quick test
    import sys
    
    print(f"PDF Support: {'✅ Enabled' if PDF_SUPPORTED else '❌ Disabled'}")
    print(f"Supported formats: .txt, .md, .markdown" + (", .pdf" if PDF_SUPPORTED else ""))
    print()
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isdir(path):
            docs = parse_directory(path)
        else:
            doc = parse_file(path)
            if doc:
                print(doc)
                print(f"\nContent preview:\n{doc.content[:500]}...")
    else:
        print("Usage: python parser.py <file_or_directory>")
