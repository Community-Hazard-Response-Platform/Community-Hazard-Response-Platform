def format_geojson_feature(row, geometry_column="geom"):
    return {
        "type": "Feature",
        "geometry": row.get(geometry_column),
        "properties": {
            key: value for key, value in row.items() if key != geometry_column
        }
    }

def format_geojson_featurecollection(rows, geometry_column="geom"):
    return {
        "type": "FeatureCollection",
        "features": [
            format_geojson_feature(row, geometry_column) for row in rows
        ]
    }

def format_geojson(rows, geometry_column="geom"):
    if not rows:
        return {"type": "FeatureCollection", "features": []}
    if len(rows) == 1:
        return format_geojson_feature(rows[0], geometry_column)
    return format_geojson_featurecollection(rows, geometry_column)
