import sys
sys.path.insert(0, 'src')
from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.get('/api/v1/health')
print('Status:', response.status_code)
import json
print(json.dumps(response.json(), indent=2))