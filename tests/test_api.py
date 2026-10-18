from concurrent.futures import ThreadPoolExecutor
import sqlite3
import pytest
from app import create_app
from scenarios import scenario

@pytest.fixture
def fixture(tmp_path):
    path=tmp_path/'plans.sqlite';return path,create_app(path)

def send(client,payload=None,key='test-request-0001'):
    return client.post('/api/plans',json=payload or scenario(0,6),headers={'Idempotency-Key':key})

def test_persist_replay_and_get(fixture):
    path,app=fixture;c=app.test_client();first=send(c);assert first.status_code==201
    replay=send(c);assert replay.status_code==200 and replay.json==first.json
    assert create_app(path).test_client().get('/api/plans/test-request-0001').json==first.json
    with sqlite3.connect(path) as db:assert db.execute('SELECT COUNT(*) FROM plans').fetchone()[0]==1

def test_reused_key_changed_body_rejected(fixture):
    c=fixture[1].test_client();send(c);changed=scenario(1,6)
    assert send(c,changed).status_code==409

def test_concurrent_same_key_one_durable_plan(fixture):
    path,app=fixture
    def request(_):return send(app.test_client())
    with ThreadPoolExecutor(max_workers=4) as pool:responses=list(pool.map(request,range(4)))
    assert all(r.status_code in [200,201] for r in responses)
    assert all(r.json==responses[0].json for r in responses)
    with sqlite3.connect(path) as db:assert db.execute('SELECT COUNT(*) FROM plans').fetchone()[0]==1

def test_missing_invalid_and_oversized(fixture):
    c=fixture[1].test_client();assert c.get('/api/plans/absent').status_code==404
    assert c.post('/api/plans',json=scenario()).status_code==400
    assert c.post('/api/plans',json={'jobs':[],'fleet':{}},headers={'Idempotency-Key':'valid-key'}).status_code==400
    assert c.post('/api/plans',data='x'*40000,content_type='application/json',headers={'Idempotency-Key':'valid-key'}).status_code==413

def test_cross_origin_post_rejected(fixture):
    r=fixture[1].test_client().post('/api/plans',json=scenario(),headers={'Idempotency-Key':'test-request-0001','Origin':'https://another-origin.example'})
    assert r.status_code==403

def test_home_health_presets_and_headers(fixture):
    c=fixture[1].test_client();r=c.get('/');assert r.status_code==200 and 'Every box' in r.text
    assert "script-src 'self'" in r.headers['Content-Security-Policy']
    assert c.get('/api/health').json=={'status':'ok'} and len(c.get('/api/scenarios').json['scenarios'])==3
