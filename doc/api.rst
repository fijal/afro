
POST /block/add

Adds a block to the list of blocks

Input:

sector: integer - ID of the sector (0 for now)
name: string - optional
description: string - optional
lat: float
lon: float

Returns:

{
    id: integer - ID of the newly created block, if status == 'OK'
    status: error | 'OK'
}

POST /block/delete

Deletes a block

Input:

id: block to delete

Returns:

{
    status: error | 'OK',
}

GET /block/list[?q=query]

Runs the query on block list. Allowed queries:

q=sector:id - returns all the blocks within a sector

Returns a list of block ids for the query

{
    id: integer - id of the block
    name: string
    description: string
    lat: float
    lon: float
    problems: list of problem ids
}

GET /block/[id]

Get a specific block

Returns:

{
    status: error | "OK"
    # rest if status == "OK"
    name: string
    sector: integer - id of the sector
    lat: float
    lon: float
    problems: list of problem ids    
}

POST /problem/add

Adds a problem to an existing block

Input:

block: integer
name: string - optional
description: string - optional
grade: string - optional

Returns:

{
    status: error | 'OK'
    id: integer - id of newly created problem if status == 'OK'
}

GET /problem/[id]

Get a specific problem

Input:

id: integer - id of the block

Returns:

{
    status: error | 'OK'
    # rest if status == "OK"
    name: string
    grade: string
    description: string
    block: integer - id of the block this problem is on
}

POST /photo/add

Add a photo

Input:

Raw data of a jpeg/png picture (taken from the content-type)

Returns:

{
    status: error | "OK"
    id: id-of-photo
}

POST /photo/associate

Associate a photo with a boulder/problem/sector

Input:

photo_id: integer - ID of a photo
type: 'boulder' | 'problem' | 'sector' | 'area'
id: ID of boulder/problem/sector/area

Returns:

{
    status: 'OK' | error
}

GET /photo/[id]

Get a specific photo

Returns:

{
    status: error | "OK"
    type: 'jpg' | 'png'
}

GET /photo/raw/[id]

Returns raw data of the photo
