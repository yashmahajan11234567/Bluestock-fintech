#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.reports.tearsheet import generate_tearsheet
import tempfile
import pypdfium2

def test_tearsheet_pages():
    """Test that tearsheet generates exactly 2 pages"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        path = f.name

    try:
        result = generate_tearsheet("TCS", path)
        print(f"Generated tearsheet: {result}")

        # Count pages
        pdf = pypdfium2.PdfDocument(path)
        n = len(pdf)
        pdf.close()
        print(f"Page count: {n}")

        if n == 2:
            print("SUCCESS: Exactly 2 pages")
            return True
        else:
            print(f"FAILURE: Expected 2 pages, got {n}")
            return False

    finally:
        if os.path.exists(path):
            os.unlink(path)

if __name__ == "__main__":
    success = test_tearsheet_pages()
    sys.exit(0 if success else 1)