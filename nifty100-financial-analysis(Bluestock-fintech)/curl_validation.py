#!/usr/bin/env python3
"""
Validate curl examples in analyst_guide.pdf

This script:
1. Extracts text from the PDF
2. Finds all curl examples
3. Validates each example against the actual API routes
4. Reports valid and invalid examples
"""

from pathlib import Path
import re
import requests
from urllib.parse import urlparse


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2

        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except ImportError:
        print("ERROR: PyPDF2 not installed. Install with: pip install PyPDF2")
        return ""
    except Exception as e:
        print(f"ERROR: Could not read PDF: {e}")
        return ""


def find_curl_examples(text: str) -> list:
    """Find all curl examples in the text."""
    # Pattern to match curl commands (handles both single and double quotes)
    pattern = r'curl\s+[^\n]+\n?(?:\s*[^\n]+)*'
    matches = re.finditer(pattern, text, re.IGNORECASE)

    curl_examples = []
    for match in matches:
        curl_text = match.group(0).strip()
        # Clean up common artifacts
        curl_text = curl_text.replace('```bash', '').replace('```', '').strip()
        curl_examples.append(curl_text)

    return curl_examples


def parse_curl_example(curl_text: str) -> dict:
    """Parse a curl example into components."""
    result = {
        'method': 'GET',
        'url': '',
        'path_params': [],
        'query_params': [],
        'headers': [],
        'is_valid': False,
        'errors': []
    }

    # Extract method and URL
    # Pattern for: curl -X METHOD 'http://...' or curl 'http://...'
    method_match = re.search(r'curl\s+-X\s+(\w+)', curl_text, re.IGNORECASE)
    if method_match:
        result['method'] = method_match.group(1).upper()

    # Extract URL (look for http:// or https://)
    url_match = re.search(r'(https?://[^\s\'\"]+)', curl_text)
    if url_match:
        result['url'] = url_match.group(1)

    # Extract path parameters from URL
    if result['url']:
        path = urlparse(result['url']).path
        # Find path parameters like {id}, :id, or <id> patterns
        path_params = re.findall(r'\{([^}]+)\}|/:([^/]+)|<([^>]+)>', path)
        result['path_params'] = [p[0] or p[1] or p[2] for p in path_params if p]

    # Extract query parameters from URL
    if result['url']:
        query = urlparse(result['url']).query
        query_params = re.findall(r'([^=&]+)=([^&]*)', query)
        result['query_params'] = [p[0] for p in query_params]

    # Check if URL is accessible
    if result['url']:
        try:
            # Make a HEAD request to check if endpoint exists (without hitting rate limits)
            response = requests.head(result['url'], timeout=5)
            if 200 <= response.status_code < 500:
                result['is_valid'] = True
            else:
                result['errors'].append(f"Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            result['errors'].append(f"Request failed: {str(e)}")

    return result


def check_against_actual_routes(curl_result: dict) -> bool:
    """Check if the curl example matches actual API routes."""
    if not curl_result['url']:
        return False

    # Parse the URL to get the path
    path = urlparse(curl_result['url']).path

    # Define known API routes from the codebase
    known_routes = [
        '/companies',
        '/companies/{company_id}',
        '/sectors',
        '/screener',
        '/peers',
        '/valuation',
        '/health',
        '/dashboard/home',
        '/api/companies',
        '/api/sectors',
        '/api/screener',
        '/api/peers',
        '/api/valuation',
        '/api/health',
    ]

    # Check if the path matches any known route pattern
    for route in known_routes:
        # Simple pattern matching
        route_pattern = route.replace('{company_id}', '[^/]+')
        route_pattern = route_pattern.replace('{id}', '[^/]+')

        if re.match(f"^{route_pattern}$", path):
            return True

    return False


def main():
    pdf_path = Path("docs/analyst_guide.pdf")

    print("PDF API CURL VALIDATION:")
    print("=" * 70)

    if not pdf_path.exists():
        print("ERROR: docs/analyst_guide.pdf not found")
        return

    print(f"Reading PDF from: {pdf_path}")

    # Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("ERROR: Could not extract text from PDF")
        return

    # Find curl examples
    print("Searching for curl examples in PDF...")
    curl_examples = find_curl_examples(text)

    print(f"Found {len(curl_examples)} curl examples")

    if not curl_examples:
        print("No curl examples found in PDF")
        return

    # Analyze each example
    valid_examples = []
    invalid_examples = []

    for i, curl_text in enumerate(curl_examples, 1):
        print(f"\n--- Example {i} ---")
        print(f"Text: {curl_text[:200]}...")

        parsed = parse_curl_example(curl_text)

        if parsed['is_valid'] and check_against_actual_routes(parsed):
            valid_examples.append({
                'number': i,
                'text': curl_text,
                'method': parsed['method'],
                'url': parsed['url'],
                'path_params': parsed['path_params'],
                'query_params': parsed['query_params']
            })
            print("✓ VALID - Matches actual API route")
        else:
            invalid_examples.append({
                'number': i,
                'text': curl_text,
                'errors': parsed['errors']
            })
            print(f"✗ INVALID - {parsed['errors'] or ['Does not match API route']}")

    # Print summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY:")
    print(f"VALID CURL EXAMPLES: {len(valid_examples)}")
    print(f"INVALID CURL EXAMPLES: {len(invalid_examples)}")

    print("\nVALID EXAMPLES:")
    for example in valid_examples:
        print(f"  Example {example['number']}: {example['method']} {example['url']}")

    if invalid_examples:
        print("\nINVALID EXAMPLES:")
        for example in invalid_examples:
            print(f"  Example {example['number']}: {example['text'][:100]}...")
            if example['errors']:
                print(f"    Errors: {example['errors']}")


if __name__ == "__main__":
    main()