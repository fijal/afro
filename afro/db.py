
from sqlalchemy import create_engine

def get_db(app, state):

    if not hasattr(state, 'con'):
        state.engine = create_engine(app.config['DATABASE'])
        state.con = state.engine.connect()
    return state.con
