
import re

from quart import request, abort
from sqlalchemy import select, func

from afro.db import get_db
from afro.model import (block, problem, photo, photo_problem, photo_block,
                        line, point)

class State:
    pass

class VerifyError(Exception):
    pass

def get_all_points(db, line_id):
    r = list(db.execute(select([point.c.index, point.c.x, point.c.y]).where(
             point.c.line_id == line_id)))
    res = [None] * len(r)
    for index, x, y in r:
        res[index] = (x, y)
    return res

def point_list_verifier(v):
    items = v.split(",")
    if len(items) % 2 != 0:
        raise VerifyError("wrong number of numbers in points, must be divisable by 2")
    if len(items) < 2:
        raise VerifyError("you need at least two points to make a line, %d supplied" % len(items))
    r = []
    for i, item in enumerate(items):
        try:
            cur = float(item)
        except ValueError:
            raise VerifyError("Not a float: %s" % item)
        if not 0.0 <= cur <= 1.0:
            raise VerifyError("%s not in range (0, 1)" % cur)
        if i % 2 == 0:
            next_item = item
        else:
            r.append((next_item, item))
    return r

def wrap(required_args=None, optional_args=None):
    def check_parameters(form):
        res_params = {}     
        if required_args is not None:
            for k, v in required_args.items():
                if k not in form:
                    raise VerifyError("parameter %s not passed" % k)
                val = form.pop(k)
                try:
                    res_params[k] = v(val)
                except (TypeError, ValueError):
                    raise VerifyError("parameter %s, value %s, expected type %s" %
                        (k, val, v.__name__))
        if optional_args is None:
            if form:
                raise VerifyError("Extra parameters passed: %s" % form)
        else:
            for k, v in form.items():
                if k not in optional_args:
                    raise VerifyError("unexpected parameter %s passed" % k)
                try:
                    res_params[k] = optional_args[k](v)
                except (TypeError, ValueError):
                    raise VerifyError("optional parameter %s, value %s, expected type %s" %
                        (k, v, optional_args[k].__name__))
        return res_params

    def inner_function(orig_func):
        async def func(*args, **kwds):
            try:
                form = (await request.form).copy()
                params = check_parameters(form)
                r = orig_func(params, *args, **kwds)
                r = (await r).copy()
                if 'status' in r:
                    return r
                r['status'] = 'OK'
                return r
            except VerifyError as e:
                return {'status': 'Verification error: %s' % e.args[0]}, 505
        func.__name__ = orig_func.__name__
        return func
    return inner_function

def register_routes(app, state):
    db = get_db(app, state)

    @app.route('/block/add', methods=['POST'])
    @wrap(required_args=dict(
        sector=int,
        lat=float,
        lon=float
    ), optional_args=dict(
        name=str,
        description=str
    ))
    async def block_add(parameters):
        r = db.execute(block.insert().values(**parameters))
        return {'id': r.inserted_primary_key[0]}

    @app.route('/block/<int:block_id>')
    async def block_get(block_id):
        q = list(db.execute(
            select([block.c.sector, block.c.name,
                block.c.lat, block.c.lon, block.c.description]).where(
                                       block.c.id == block_id)))
        if len(q) == 0:
            return {'status': 'no block id %s found' % block_id}, 505
        assert len(q) == 1
        q = list(q[0])
        prob_q = list(db.execute(
            select([problem.c.id]).where(problem.c.block == block_id)))
        problems = [x[0] for x in prob_q]
        return {"status": 'OK', 'sector': q[0], 'name': q[1],
                'lat': q[2], 'lon': q[3], 'problems': problems,
                'description': q[4]}

    @app.route('/block/<int:block_id>', methods=['POST'])
    @wrap(required_args={}, optional_args=dict(
        name=str, description=str, lat=float, lon=float
        ))
    async def block_update(parameters, block_id):
        q = list(db.execute(
            select([block.c.sector, block.c.name,
                block.c.lat, block.c.lon, block.c.description]).where(
                                       block.c.id == block_id)))
        if len(q) == 0:
            return {'status': 'no block id %s found' % block_id}, 505
        assert len(q) == 1

        db.execute(
            block.update().where(block.c.id == block_id).values(**parameters))
        return {'status': "OK"}

    @app.route('/block/<int:block_id>/photos')
    async def block_get_photos(block_id):
        q = list(db.execute(select([block.c.id]).where(
            block.c.id == block_id)))
        if len(q) == 0:
            return {'status': 'no block id %d found' % block_id}, 505
        q = list(db.execute(select([photo_block.c.photo]).where(
                 photo_block.c.block == q[0][0])))
        return {'status': 'OK', 'photos': [x[0] for x in q]}

    @app.route('/block/list')
    async def block_list():
        if 'q' not in request.args:
            return {'status': 'Query not passed, please pass q parameter'}, 505
        m = re.match(r'^sector:(\d+)$', request.args['q'])
        if not m:
            return {'status': 'Unsupported query - %s' % request.args['q']}, 505
        sector_id = int(m.group(1))
        l = list(db.execute(select([block.c.id, block.c.name, block.c.description,
            block.c.lat, block.c.lon]).where(block.c.sector == sector_id)))
        r = []
        for id, name, description, lat, lon in l:
            r.append({
                'id': id,
                'name': name,
                'description': description,
                'lat': lat,
                'lon': lon
                })
        return {'status': 'OK', 'blocks': r}

    @app.route('/block/delete', methods=['POST'])
    @wrap(required_args=dict(id=int))
    async def block_delete(parameters):
        block_id = parameters['id']
        q = list(db.execute(select([block.c.id]).where(
            block.c.id == block_id)))
        if len(q) == 0:
            return {'status': 'no block id %d found' % block_id}, 505
        db.execute(block.delete().where(block.c.id == block_id))
        return {'status': 'OK'}

    @app.route('/problem/add', methods=['POST'])
    @wrap(required_args=dict(block=int), optional_args=dict(
        name=str,
        description=str,
        grade=str
    ))
    async def problem_add(parameters):
        r = db.execute(problem.insert().values(**parameters))
        return {'id': r.inserted_primary_key[0]}

    @app.route('/problem/<int:problem_id>')
    async def problem_get(problem_id):
        q = list(db.execute(
            select([problem.c.block, problem.c.name, problem.c.description,
            problem.c.grade]).where(problem.c.id == problem_id)))
        if len(q) == 0:
            return {'status': 'no problem id %s found' % problem_id}, 505
        assert len(q) == 1
        q = list(q[0])
        return {"status": 'OK', 'block': q[0], 'name': q[1],
                'description': q[2], 'grade': q[3]}

    @app.route('/problem/<int:problem_id>/photos')
    async def problem_get_photos(problem_id):
        q = list(db.execute(select([problem.c.id]).where(
            problem.c.id == problem_id)))
        if len(q) == 0:
            return {'status': 'no problem id %d found' % problem_id}, 505
        q = list(db.execute(select([photo_problem.c.photo]).where(
                 photo_problem.c.problem == q[0][0])))
        return {'status': 'OK', 'photos': [x[0] for x in q]}

    @app.route('/photo/add', methods=['POST'])
    async def photo_add():
        data = await request.data
        r = list(db.execute(select([func.count(photo)])))
        last_photo = r[0][0]
        photo_file = "photo%d.jpg" % (last_photo,)
        with app.config['tmpdir'].join(photo_file).open('wb') as f:
            f.write(data)
        db.execute(photo.insert().values({'filename': photo_file}))
        return {'status': 'OK', 'filename': photo_file}

    @app.route('/photo/associate', methods=['POST'])
    @wrap(required_args=dict(photo_filename=str, id=int, type=str))
    async def photo_associate(parameters):
        photo_filename = parameters['photo_filename']
        q = list(db.execute(select([photo.c.filename]).where(
            photo.c.filename == photo_filename)))
        if len(q) == 0:
            return {'status': 'photo %s not found' % photo_filename}, 505
        tp = parameters['type']
        id = parameters['id']
        if tp == 'problem':
            q = list(db.execute(select([problem.c.id]).where(
                problem.c.id == id)))
            if len(q) == 0:
                return {'status': 'unknown problem id %d' % id}, 505
            db.execute(photo_problem.insert().values({
                'photo': photo_filename,
                'problem': id
                }))
            return {'status': 'OK'}
        elif tp == 'block':
            q = list(db.execute(select([block.c.id]).where(
                block.c.id == id)))
            if len(q) == 0:
                return {'status': 'unknown block id %d' % id}, 505
            db.execute(photo_block.insert().values({
                'photo': photo_filename,
                'block': id
                }))
            return {'status': 'OK'}
        else:
            return {'status': 'unknown type %s' % parameters['type']}, 505

    @app.route('/photo/<photo_filename>')
    async def photo_get(photo_filename):
        q = list(db.execute(select([photo.c.filename]).where(
            photo.c.filename == photo_filename)))
        if len(q) == 0:
            return {'status': 'photo not found'}, 505
        lines = list(db.execute(select([line.c.id, line.c.problem]).where(
            line.c.photo == photo_filename)))
        return {'status': 'OK', 'type': 'jpg', 'lines': [
            {
                'id': line_id,
                'problem': problem_id,
                'points': get_all_points(db, line_id)
            } for (line_id, problem_id) in lines]
        }

    @app.route('/photo/raw/<photo_filename>')
    async def photo_raw_get(photo_filename):
        q = list(db.execute(select([photo.c.filename]).where(
            photo.c.filename == photo_filename)))
        if len(q) == 0:
            return "", 404
        return open(app.config['tmpdir'].join(photo_filename), 'rb').read()

    @app.route('/line/add', methods=['POST'])
    @wrap(required_args=dict(
        problem=int,
        point_list=point_list_verifier,
        photo_filename=str
        ))
    async def line_add(parameters):
        problem_id = parameters['problem']
        photo_filename = parameters['photo_filename']
        r = list(db.execute(select([problem.c.id]).where(problem.c.id == problem_id)))
        if len(r) == 0:
            return {'status': "can't find problem id %d" % problem_id}, 505
        r = list(db.execute(select([photo.c.filename]).where(photo.c.filename == photo_filename)))
        if len(r) == 0:
            return {'status': "can't find photo filename %s" % photo_filename}, 505
        r = db.execute(line.insert().values({
            'problem': problem_id,
            'photo': photo_filename
            }))
        line_id = r.lastrowid
        for i, (x, y) in enumerate(parameters['point_list']):
            db.execute(point.insert().values({
                'line_id': line_id,
                'index': i,
                'x': x,
                'y': y
                }))
        return {'status': 'OK', 'id': line_id}

    @app.route('/line/<int:line_id>')
    async def line_get(line_id):
        r = list(db.execute(select([line.c.id]).where(line.c.id == line_id)))
        if len(r) == 0:
            return {'status': "can't find line ID %d" % line_id}, 505
        points = get_all_points(db, line_id)
        return {'status': 'OK', 'points': points}

    return app
