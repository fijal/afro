
import pytest, json
from quart import Quart

from afro.db import get_db
from afro.model import meta
from afro.api import register_routes, State

def init_db(state):
    meta.create_all(state.engine)

@pytest.fixture
def db(tmpdir):
    app = Quart("afro")
    app.config['DATABASE'] = 'sqlite:///:memory:'
    state = State()
    get_db(app, state)
    init_db(state)
    register_routes(app, state)
    return app

class Error(Exception):
    pass

async def post(client, url, form=None):
    resp = await client.post(url, form=form)
    if resp.status_code != 200:
        raise Error(resp.status_code)
    r = json.loads((await resp.get_data()).decode('utf8'))
    if r['status'] != 'OK':
        raise Error(r['status'])
    return r

async def get(client, url):
    resp = await client.get(url)
    assert resp.status_code == 200
    r = json.loads((await resp.get_data()).decode('utf8'))
    if r['status'] != 'OK':
        raise Error(r['status'])
    return r

@pytest.mark.asyncio
async def test_parameter_passing(db):
    client = db.test_client()
    
    resp = await client.post('/block/add')
    assert resp.status_code == 200
    r = json.loads((await resp.get_data()).decode('utf8'))
    assert 'Verification error' in r['status']
    
    resp = await(client.post('/block/add', form={'sector': 'foo'}))
    r = json.loads((await resp.get_data()).decode('utf8'))
    assert 'value foo, expected type int' in r['status']

    resp = await(client.post('/block/add', form={'sector': '0',
        'lat': '0', 'lon': '0', 'other': 'foo'}))
    r = json.loads((await resp.get_data()).decode('utf8'))
    assert 'unexpected parameter other' in r['status']

    resp = await(client.post('/block/add', form={'sector': '0',
        'name': 'foo', 'lat': '32.15', 'lon': '15.36'}))
    r = json.loads((await resp.get_data()).decode('utf8'))
    assert r['status'] == 'OK'
    assert r['id'] == 1

@pytest.mark.asyncio
async def test_block_problem(db):
    client = db.test_client()

    r = await post(client, '/block/add', form={'sector': '0',
        'name': 'foo', 'lat': '32.15', 'lon': '15.36'})
    block_id = r['id']
    r = await post(client, '/problem/add', form=dict(
        block=block_id, name="foo bar"
        ))
    problem_id = r['id']
    resp = await client.get('/problem/%s' % (problem_id + 14))
    assert resp.status_code == 200
    r = json.loads((await resp.get_data()).decode('utf8'))
    assert r['status'] != 'OK'

    r = await get(client, '/problem/%s' % problem_id)
    assert r == {'status': 'OK', 'block': block_id, 'grade': None,
                 'name': 'foo bar',
                 'description': None}

    r = await get(client, '/block/%s' % block_id)
    assert r == {'status': 'OK', 'sector': 0, 'lat': 32.15, 'lon': 15.36,
                 'name': 'foo', 'problems': [problem_id]}


