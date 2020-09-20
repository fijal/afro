
from sqlalchemy import (Table, Column, Integer, Boolean,
    String, MetaData, ForeignKey, create_engine, Float)

meta = MetaData()

area = Table('area', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String),
    Column('description', String),
    Column('lat', Float),
    Column('lon', Float)
)

sector = Table('sector', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('area', Integer, ForeignKey('area.id')),
    Column('name', String),
    Column('description', String),
    Column('lat', Float),
    Column('lon', Float)
)

block = Table('block', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('sector', Integer, ForeignKey('sector.id')),
    Column('name', String),
    Column('description', String),
    Column('lat', Float),
    Column('lon', Float)
)

problem = Table('problem', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('block', Integer, ForeignKey('block.id')),
    Column('name', String),
    Column('description', String),
    Column('grade', String)
)

photo = Table('photo', meta,
    Column('filename', String, primary_key=True)
)

photo_problem = Table('photo_problem', meta,
    Column('photo', String, ForeignKey('photo.filename')),
    Column('problem', Integer, ForeignKey('problem.id'))
)

photo_block = Table('photo_block', meta,
    Column('photo', String, ForeignKey('photo.filename')),
    Column('block', Integer, ForeignKey('block.id'))
)

line = Table('line', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('photo', String, ForeignKey('photo.filename')),
    Column('problem', Integer, ForeignKey('problem.id'))
)

point = Table('point', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('line_id', Integer, ForeignKey('line.id')),
    Column('x', Float),
    Column('y', Float),
    Column('index', Integer)
)

# describe a line on the photo linked to a specific problem
#polyline = Table('polyline')

if __name__ == '__main__':
    def metadata_dump(sql, *multiparams, **params):
        # print or write to log or file etc
        print(sql.compile(dialect=engine.dialect))

    engine = create_engine('sqlite:///:memory:', strategy='mock', executor=metadata_dump)
    meta.create_all(engine)

