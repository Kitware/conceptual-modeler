def parse_grid_csv(content):
    header, content, *_ = content.decode("utf-8").split("\n")
    keys = header.split(",")
    values = content.split(",")
    data = dict(zip(keys, values))
    print(data)
    return {
        "extent": [
            float(data.get("xmin", 0)),
            float(data.get("xmax", 1)),
            float(data.get("ymin", 0)),
            float(data.get("ymax", 1)),
            float(data.get("zmin", 0)),
            float(data.get("zmax", 1)),
        ],
        "resolution": [
            int(data.get("nx", 10)),
            int(data.get("ny", 10)),
            int(data.get("nz", 10)),
        ],
    }
