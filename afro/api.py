
from quart import request
from sqlalchemy import select

from afro.db import get_db
from afro.model import block, problem

class State:
    pass

class VerifyError(Exception):
    pass

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
                r['status'] = 'OK'
                return r
            except VerifyError as e:
                return {'status': 'Verification error: %s' % e.args[0]}
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
                block.c.lat, block.c.lon])))
        if len(q) == 0:
            return {'status': 'no block id %s found' % block_id}
        assert len(q) == 1
        q = list(q[0])
        prob_q = list(db.execute(
            select([problem.c.id]).where(problem.c.block == block_id)))
        problems = [x[0] for x in prob_q]
        return {"status": 'OK', 'sector': q[0], 'name': q[1],
                'lat': q[2], 'lon': q[3], 'problems': problems}

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
            return {'status': 'no problem id %s found' % problem_id}
        assert len(q) == 1
        q = list(q[0])
        return {"status": 'OK', 'block': q[0], 'name': q[1],
                'description': q[2], 'grade': q[3]}

    return app
