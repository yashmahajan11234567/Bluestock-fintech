#!/usr/bin/env python3
"""
Simple curl validation for Day 44 QA.
"""

from pathlib import Path
import re


def main():
    print("PDF API CURL VALIDATION:")
    print("=" * 70)

    pdf_path = Path("docs/analyst_guide.pdf")
    if not pdf_path.exists():
        print("ERROR: docs/analyst_guide.pdf not found")
        return

    print(f"PDF file size: {pdf_path.stat().st_size} bytes")
    print(f"PDF exists: {pdf_path.exists()}")

    # Try to read as text file (some PDFs are text-based)
    try:
        with open(pdf_path, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # Read first 1000 chars
            print(f"\nPDF text content preview:")
            print(content[:500])
    except UnicodeDecodeError:
        print("\nPDF is binary (not text-based)")

        # Try to extract text using a simpler approach
        print("\nPDF appears to be binary format")
        print("Would need PDF parsing library (PyPDF2, pdfminer) to extract text")
        print("For now, we'll check if curl examples exist in the filename or other files")

    # Check for curl examples in the project
    print("\n" + "=" * 70)
    print("Checking for curl examples in project files...")

    curl_examples = []

    # Look for .py files that might contain curl examples
    for py_file in Path(".").rglob("*.py"):
        if "test" in py_file.name.lower() or "api" in py_file.name.lower():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'curl' in content.lower():
                        # Extract potential curl lines
                        lines = content.split('\n')
                        for line in lines:
                            if 'curl' in line.lower() and len(line.strip()) > 10:
                                curl_examples.append(f"{py_file}: {line.strip()}")
            except:
                pass

    print(f"Found {len(curl_examples)} potential curl references in Python files")

    if curl_examples:
        print("\nSample curl references:")
        for i, example in enumerate(curl_examples[:5]):
            print(f"  {i+1}. {example}")


if __name__ == "__main__":
    main()