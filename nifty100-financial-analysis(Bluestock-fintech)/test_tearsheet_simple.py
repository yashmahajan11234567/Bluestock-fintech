import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.reports.tearsheet import generate_tearsheet
import tempfile

# Test TCS tearsheet generation
with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
    path = f.name

try:
    result = generate_tearsheet("TCS", path)
    print(f"Tearsheet generated: {result}")
    print(f"File exists: {os.path.exists(path)}")
    print(f"File size: {os.path.getsize(path)} bytes")

    # Try to get page count if pypdfium2 is available
    try:
        import pypdfium2
        pdf = pypdfium2.PdfDocument(path)
        n = len(pdf)
        pdf.close()
        print(f"Page count: {n}")
    except ImportError:
        print("pypdfium2 not available for page count")

finally:
    if os.path.exists(path):
        os.unlink(path)