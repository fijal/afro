
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

POST /block/[id]

Update a specific block

Input:

id: integer - ID of the block to update
name: string - optional - change the name
description: string - optional - change the description
lat: float - optional - change the lattitude
lon: float - optional - change the longitude

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

Returns:
{
    status: error | 'OK'
    // list of blocks
    blocks: [{
        id: integer - id of the block
        name: string
        description: string
        lat: float
        lon: float
    }]
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

GET /block/[id]/photos

Get a list of photos for a specific block

Input:

id: integer - ID of the block

Returns:

{
    status: error | "OK"
    photos: list of strings - list of photo filenames    
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

id: integer - id of the problem

Returns:

{
    status: error | 'OK'
    # rest if status == "OK"
    name: string
    grade: string
    description: string
    block: integer - id of the block this problem is on
}

GET /problem/[id]/photos

Get a list of photos associated with a given problem

Input:

id: integer - id of the problem

Returns:

{
    status: error | "OK"
    photos: list of strings - list of photo filenames
}

POST /photo/add

Add a photo

Input:

Raw data of a jpeg/png picture (taken from the content-type)

Returns:

{
    status: error | "OK"
    filename: str - photo filename
}

POST /photo/associate

Associate a photo with a boulder/problem/sector

Input:

photo_filename: str - photo filename
type: 'boulder' | 'problem' | 'sector' | 'area'
id: int - ID of boulder/problem/sector/area

Returns:

{
    status: 'OK' | error
}

GET /photo/[filename]

Get a specific photo

Returns:

{
    status: error | "OK"
    lines: list of lines. Each line is of following:
    {
        id: int - id
        problem: int - problem id
        points: list of tuples of floats describing line points
    }
    type: 'jpg' | 'png'
}

GET /photo/raw/[filename]

Returns raw data of the photo

POST /line/add

Add a new line to existing photo

Input:

photo_filename: string - filename of the photo that we are associating
                         the line with
problem: int - id of the problem associated with that line
point_list: list_of_float_points - list of points on the picture
            The list is a comma separate list of float values of x and y in range
            between 0 and 1, where 0,0 means left top and 1,1 means right bottom.
            So for example two points, (0.5, 0.4) and (0.2, 0.1) would be
            0.5,0.5,0.2,0.1

Returns:

{
    status: 'OK' | error
    id: int - ID of a newly created line
}

GET /line/[id]

Get a specific line

Returns:

{
    status: 'OK' | error
    points: list_of_float_tuples - list of points grouped by (x, y), so
            [(x0, y0), (x1, y1), (x2, y2)] etc.
}

