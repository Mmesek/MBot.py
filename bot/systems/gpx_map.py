import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import gpxpy
import gpxpy.gpx
import httpx
import orjson as json
from mlib import graphing


def convert_to_geojson(overpass_data):
    features = []
    nodes_dict = {}

    # First, create a dictionary of nodes for easy access
    for element in overpass_data.get("elements", []):
        if element["type"] == "node":
            nodes_dict[element["id"]] = [element["lon"], element["lat"]]  # Store as [longitude, latitude]

    # Now, convert ways to GeoJSON LineStrings
    for element in overpass_data.get("elements", []):
        if element["type"] == "way":
            coordinates = [nodes_dict[node_id] for node_id in element["nodes"] if node_id in nodes_dict]
            if coordinates:
                feature = {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coordinates},
                    "properties": {"id": element["id"]},
                }
                features.append(feature)

    geojson = {"type": "FeatureCollection", "features": features}

    return geojson


async def fetch_street_data(bbox):
    # Define the Overpass API endpoint
    overpass_url = "http://overpass-api.de/api/interpreter"

    # Create the Overpass QL query
    bbox_query = f"""
    [out:json];
    (
        way["highway"~"residential|tertiary|secondary|primary|unclassified"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
        node(w);
        relation["highway"~"residential|tertiary|secondary|primary|unclassified"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
    );
    out body;
    out skel qt;
    convert item ::=::,::geom=geom(),_osm_type=type();
    """

    # Send the request to the Overpass API
    async with httpx.AsyncClient() as client:
        response = await client.get(overpass_url, params={"data": bbox_query})

    # Check if the request was successful
    if response.status_code == 200:
        buffer = json.dumps(convert_to_geojson(response.json()))
        return gpd.read_file(buffer)  # .getvalue())

    else:
        raise Exception(f"Error fetching data: {response.status_code}")


async def map(g: gpxpy.gpx.GPX):
    b = g.get_bounds()
    world = await fetch_street_data([b.min_longitude, b.min_latitude, b.max_longitude, b.max_latitude])

    data = {"latitude": [], "longitude": [], "speed": [], "age": [], "time": []}
    for track in g.tracks:
        for segment in track.segments:
            last_point = None
            for point in segment.points:
                if (
                    point.speed
                    or last_point
                    and (last_point.latitude != point.latitude and last_point.longitude != point.longitude)
                ):
                    data["latitude"].append(point.latitude)
                    data["longitude"].append(point.longitude)
                    data["speed"].append(point.speed)
                    data["age"].append(point.age_of_dgps_data)
                    data["time"].append(point.time)

                last_point = point
    df = pd.DataFrame(data)
    df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["longitude"], df["latitude"]), crs="EPSG:4326")
    df.set_index("time")

    plt.style.use("./pine.mplstyle")
    fig, ax = plt.subplots(figsize=(12, 8))

    world.plot(ax=ax, color="#363636", edgecolor="black")
    data = list(df.iterrows())
    for idx, row in data:
        if idx > 0:
            ax.plot(
                [row.geometry.x, data[idx - 1][1].geometry.x],
                [row.geometry.y, data[idx - 1][1].geometry.y],
                color="#0281f8",
            )

    # Set map boundaries
    ax.set_xlim(b.min_longitude, b.max_longitude)  # Longitude range
    ax.set_ylim(b.min_latitude, b.max_latitude)  # Latitude range

    plt.title("Approximate Travel Route")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()
    return graphing.create_image(fig)
