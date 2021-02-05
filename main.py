
""" Usage:

main.py PORT DB_FILE
"""
import sys
from quart import Quart

from afro.api import register_routes, State

app = Quart("afro")

if len(sys.argv) != 3:
    print(__doc__)
    sys.exit(1)

port = int(sys.argv[1])
db_file = sys.argv[2]

app.config.update({
    'DATABASE': 'sqlite:///' + str(app.root_path / db_file),
})

if __name__ == '__main__':
    state = State()
    app = register_routes(app, state)
    app.run(port=port)
