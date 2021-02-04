
import pytest, json, py
from quart import Quart

from afro.db import get_db
from afro.model import meta
from afro.api import register_routes, State

def init_db(state):
    meta.create_all(state.engine)

@pytest.fixture
def db():
    app = Quart("afro")
    app.config['DATABASE'] = 'sqlite:///:memory:'
    state = State()
    get_db(app, state)
    init_db(state)
    register_routes(app, state)
    return app

class Error(Exception):
    pass

async def post(client, url, form=None, data=None):
    resp = await client.post(url, form=form, data=data)
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
                 'name': 'foo', 'problems': [problem_id], 'description': None}

    r = await post(client, '/block/delete', form={'id': block_id})
    assert r == {'status': 'OK'}
    r = await client.get('/block/%s' % block_id)
    r = json.loads((await r.get_data()).decode('utf8'))
    assert r['status'] != 'OK'

@pytest.mark.asyncio
async def test_pictures(db, tmpdir):
    client = db.test_client()

    r = await post(client, '/block/add', form={'sector': '0',
        'name': 'foo', 'lat': '32.15', 'lon': '15.36'})
    block_id = r['id']
    r = await post(client, '/problem/add', form=dict(
        block=block_id, name="foo bar"
        ))
    problem_id = r['id']
    db.config['tmpdir'] = tmpdir
    r = await post(client, '/photo/add', data=b"foobarbaz")
    assert r['filename'] == 'photo0.jpg'
    r = await get(client, '/photo/photo0.jpg')
    assert r['type'] == 'jpg'
    r = await client.get('/photo/raw/photo0.jpg')
    assert (await r.get_data()) == b'foobarbaz'

    await post(client, '/photo/associate', form={
        'photo_filename': 'photo0.jpg',
        'type': 'problem',
        'id': problem_id
        })

    r = await get(client, '/problem/%d/photos' % problem_id)
    assert r['photos'] == ['photo0.jpg']

    await post(client, '/photo/associate', form={
        'photo_filename': 'photo0.jpg',
        'type': 'block',
        'id': block_id
        })

    r = await get(client, '/block/%d/photos' % block_id)

    assert r['photos'] == ['photo0.jpg']

@pytest.mark.asyncio
async def test_lines(db, tmpdir):
    client = db.test_client()

    r = await post(client, '/block/add', form={'sector': '0',
        'name': 'foo', 'lat': '32.15', 'lon': '15.36'})
    block_id = r['id']
    r = await post(client, '/problem/add', form=dict(
        block=block_id, name="foo bar"
        ))
    problem_id = r['id']
    db.config['tmpdir'] = tmpdir
    r = await post(client, '/photo/add', data=b"foobarbaz")
    assert r['filename'] == 'photo0.jpg'

    r = await post(client, '/line/add', form=dict(
        photo_filename='photo0.jpg', problem=problem_id,
        point_list="0.1,0.2,0.3,0.4"
        ))
    assert r['status'] == 'OK'
    line_id = r['id']

    r = await get(client, '/line/%d' % line_id)
    assert r['status'] == 'OK'
    assert r['points'] == [[0.1, 0.2], [0.3, 0.4]]

    r = await get(client, '/photo/photo0.jpg')
    assert r['status'] == 'OK'
    assert r['lines'] == [{'id': 1, 'problem': problem_id,
       'points': [[0.1, 0.2], [0.3, 0.4]]}]

@pytest.mark.asyncio
async def test_boulder_list(db):
    client = db.test_client()

    r = await post(client, '/block/add', form={'sector': '0',
        'name': 'foo', 'description': 'some descr', 'lat': '32.15', 'lon': '15.36'})
    block_id = r['id']

    r = await get(client, '/block/list?q=sector:0')
    assert r['blocks'] == [
        {'id': block_id, 'name': 'foo', 'description': 'some descr', 'lat': 32.15, 'lon': 15.36}
    ]
    r = await post(client, '/block/add', form={'sector': '0',
        'name': 'foo2', 'description': 'some descr2', 'lat': '2.15', 'lon': '5.36'})
    block2_id = r['id']
    r = await get(client, '/block/list?q=sector:0')
    assert r['blocks'] == [
        {'id': block_id, 'name': 'foo', 'description': 'some descr', 'lat': 32.15, 'lon': 15.36},
        {'id': block2_id, 'name': 'foo2', 'description': 'some descr2', 'lat': 2.15, 'lon': 5.36}
    ]
