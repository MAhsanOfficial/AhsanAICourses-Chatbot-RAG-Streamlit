from fastapi.testclient import TestClient
from backend.app import app
import json

client = TestClient(app)

print('Health', client.get('/health').status_code, client.get('/health').json())

lead = {"name":"Test User","email":"test@example.com","phone":"123","interest":"Data Science"}
print('/lead', client.post('/lead', json=lead).status_code, client.post('/lead', json=lead).json())
print('/chat', client.post('/chat', json={'session_id':'s','message':'hi'}).status_code, client.post('/chat', json={'session_id':'s','message':'hi'}).json())
print('/admin/leads', client.get('/admin/leads').status_code, client.get('/admin/leads').json())
print('/kb/search', client.post('/kb/search', json={'query':'data science','top_k':2}).status_code, client.post('/kb/search', json={'query':'data science','top_k':2}).json())
