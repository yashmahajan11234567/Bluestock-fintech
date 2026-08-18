import sys
sys.path.insert(0, 'src')
from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.get('/api/v1/health')

# Write result to file
import json
with open('health_response.json', 'w') as f:
    json.dump({
        'status_code': response.status_code,
        'response': response.json(),
        'headers': dict(response.headers)
    }, f, indent=2)
print("Result written to health_response.json")