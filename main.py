
from quart import Quart

from afro.api import register_routes, State

app = Quart("afro")

app.config.update({
    'DATABASE': 'sqlite:///' + str(app.root_path / 'afro.db'),
})

if __name__ == '__main__':
    state = State()
    app = register_routes(app, state)
    app.run()
