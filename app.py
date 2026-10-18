"""Local planning API with durable, idempotent result storage."""
import hashlib, json, os, re, sqlite3, time
from pathlib import Path
from urllib.parse import urlsplit
from flask import Flask, request, jsonify, render_template
from planner import plan, validate
from scenarios import presets

def create_app(database=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024
    path = str(database or os.environ.get('RESCUE_DB', Path(__file__).parent / 'var/plans.sqlite'))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS plans (id TEXT PRIMARY KEY, digest TEXT NOT NULL, result TEXT NOT NULL, created REAL NOT NULL)')
    @app.before_request
    def same_origin():
        origin = request.headers.get('Origin')
        if request.method == 'POST' and origin and urlsplit(origin).netloc != request.host:
            return jsonify(error='Use the local app origin'), 403
    @app.after_request
    def headers(response):
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-store'
        return response
    @app.errorhandler(ValueError)
    def invalid(error): return jsonify(error=str(error)), 400
    @app.errorhandler(413)
    def large(error): return jsonify(error='Scenario exceeds 32 KB'), 413
    @app.get('/')
    def home(): return render_template('index.html')
    @app.get('/api/scenarios')
    def examples(): return jsonify(scenarios=presets())
    @app.get('/api/health')
    def health():
        with sqlite3.connect(path) as db: db.execute('SELECT 1 FROM plans LIMIT 1').fetchone()
        return jsonify(status='ok')
    @app.post('/api/plans')
    def create_plan():
        key = request.headers.get('Idempotency-Key', '')
        if not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', key):
            return jsonify(error='Provide an 8–64 character Idempotency-Key'), 400
        payload = validate(request.get_json())
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        with sqlite3.connect(path, timeout=10) as db:
            old = db.execute('SELECT digest,result FROM plans WHERE id=?', (key,)).fetchone()
        if old:
            if old[0] != digest: return jsonify(error='This request key belongs to a different scenario'), 409
            return jsonify(json.loads(old[1])), 200
        result = {'id': key, **plan(payload)}
        encoded = json.dumps(result, allow_nan=False)
        with sqlite3.connect(path, timeout=10) as db:
            db.execute('INSERT OR IGNORE INTO plans VALUES(?,?,?,?)', (key, digest, encoded, time.time()))
            saved = db.execute('SELECT digest,result FROM plans WHERE id=?', (key,)).fetchone()
        if saved[0] != digest: return jsonify(error='This request key belongs to a different scenario'), 409
        return jsonify(json.loads(saved[1])), 201
    @app.get('/api/plans/<key>')
    def get_plan(key):
        with sqlite3.connect(path) as db: result = db.execute('SELECT result FROM plans WHERE id=?', (key,)).fetchone()
        return (jsonify(json.loads(result[0])), 200) if result else (jsonify(error='Plan not found'), 404)
    return app

app = create_app()
if __name__ == '__main__': app.run(host='127.0.0.1', port=int(os.environ.get('PORT', '8081')))
