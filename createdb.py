
""" createdb.py [DB URL]
"""

import sys
from sqlalchemy import create_engine

from afro.model import meta

if __name__ == '__main__':
    db_url = sys.argv[1]
    engine = create_engine(db_url)
    engine.connect()
    meta.create_all(engine)
