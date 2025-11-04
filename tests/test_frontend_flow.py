import requests
import json

BASE = "http://127.0.0.1:8000"

def p(r):
    try:
        print(r.status_code)
        print(json.dumps(r.json(), indent=2, default=str))
    except Exception:
        print(r.status_code, r.text[:1000])

print('Health:')
try:
    p(requests.get(BASE + '/health'))
except Exception as e:
    print('health err', e)

print('\nSubmit lead:')
lead = {"name":"Test User","email":"test@example.com","phone":"123","interest":"Data Science"}
try:
    r = requests.post(BASE + '/lead', json=lead, timeout=10)
    p(r)
except Exception as e:
    print('lead err', e)

print('\nChat:')
try:
    r = requests.post(BASE + '/chat', json={'session_id':'test-session','message':'Tell me about Data Science course.'}, timeout=15)
    p(r)
except Exception as e:
    print('chat err', e)

print('\nAdmin leads:')
try:
    r = requests.get(BASE + '/admin/leads', timeout=10)
    p(r)
except Exception as e:
    print('admin err', e)

print('\nKB search:')
try:
    r = requests.post(BASE + '/kb/search', json={'query':'data science','top_k':2}, timeout=10)
    p(r)
except Exception as e:
    print('kb err', e)
