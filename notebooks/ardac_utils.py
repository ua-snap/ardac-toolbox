import requests
import json
import pandas as pd
import geopandas as gpd
import shapely
from zipfile import ZipFile
from lxml import etree as ET


valid_areas = [
    "communities",
    "hucs",
    "protected_areas",
    "corporations",
    "climate_divisions",
    "fire_zones",
    "ethnolinguistic_regions",
    "boroughs",
    "census_areas",
    "game_management_units",
    "first_nations",
]

has_zonal_stats = {
    "indicators": "indicators/base/area/",
    "beetles": "beetles/area/",
    #'elevation':'elevation/area/', <<< elevation data has no csv output option!
    "flammability": "alfresco/flammability/area/",
    "veg_type": "alfresco/veg_type/area/",
    "temperature": "temperature/area/",
    "precipitation": "precipitation/area/",
    "temperature_and_precipitation": "taspr/area/",
}


def get_point_gdf_by_category(category_string):
    # if category is 'communities' simply return a gdf using lat/lon ... output in 4326 so the lat/lons can be used in API querys
    # if category is not community, compute the centroid of the polygons returned ... output in 4326 so the lat/lons can be used in API querys
    if category_string not in valid_areas:
        message = "Bad category string. Choose one of the following: "
        return print(message, valid_areas)

    else:
        with requests.Session() as s:
            response = s.get("https://earthmaps.io/places/" + category_string)
            response_json_list = response.json()

        if response.status_code != 200:
            return "bad request"

        if category_string == "communities":
            places_df = pd.DataFrame(
                columns=["id", "name", "country", "latitude", "longitude"]
            )

            for place in response_json_list:
                new_row = [
                    place["id"],
                    place["name"],
                    place["country"],
                    place["latitude"],
                    place["longitude"],
                ]
                places_df.loc[
                    len(places_df.index),
                    ["id", "name", "country", "latitude", "longitude"],
                ] = new_row
                places_df["the_geom"] = gpd.points_from_xy(
                    places_df.longitude, places_df.latitude
                )
                gdf_output = gpd.GeoDataFrame(places_df, geometry="the_geom", crs=4326)

            return gdf_output

        else:
            area_gdfs = []
            for item in response_json_list:
                id, name = item["id"], item["name"]
                with requests.Session() as s:
                    area_poly_response = s.get(
                        str("https://earthmaps.io/boundary/area/" + str(id))
                    )
                    if area_poly_response.status_code != 200:
                        print("bad request")
                    else:
                        geojson = area_poly_response.json()
                        geojson["the_geom"] = shapely.from_geojson(json.dumps(geojson))
                        gdf = (
                            gpd.GeoDataFrame([geojson])
                            .set_geometry("the_geom")
                            .set_crs(4326)
                        )
                        gdf.drop(
                            columns=["geometry", "properties", "type"], inplace=True
                        )
                        gdf["id"], gdf["name"] = id, name

                        name_col = gdf.pop("name")
                        gdf.insert(1, "name", name_col)
                        area_gdfs.append(gdf)

            gdf_output = pd.concat(area_gdfs)

            # convert to 3338 to get centroid, then convert x and y coords back to 4326 to add get lat/lon attributes
            gdf_3338 = gdf_output.to_crs(3338)
            gdf_3338["the_geom"] = gdf_3338["the_geom"].centroid
            gdf_output = gdf_3338.to_crs(4326)
            gdf_output["latitude"] = gdf_output.geometry.y
            gdf_output["longitude"] = gdf_output.geometry.x
            geom_col = gdf_output.pop("the_geom")
            gdf_output.insert(len(gdf_output.columns), "the_geom", geom_col)

            return gdf_output


def get_area_gdf_by_category(area_category_string, crs_code=None):
    if (crs_code != None) & (type(crs_code) != int):
        return print("CRS code must be EPSG as integer.")

    if area_category_string not in valid_areas[1:]:
        message = "Bad area category string. Choose one of the following: "
        return print(message, valid_areas[1:])
    else:
        with requests.Session() as s:
            area_names_response = s.get(
                "https://earthmaps.io/places/" + area_category_string
            )
            area_names_json_list = area_names_response.json()

        if area_names_response.status_code != 200:
            return "bad request"
        else:
            area_gdfs = []
            for area in area_names_json_list:
                id, name = area["id"], area["name"]
                with requests.Session() as s:
                    area_poly_response = s.get(
                        str("https://earthmaps.io/boundary/area/" + str(id))
                    )
                    if area_poly_response.status_code != 200:
                        print("bad request")
                    else:
                        geojson = area_poly_response.json()
                        geojson["the_geom"] = shapely.from_geojson(json.dumps(geojson))
                        gdf = (
                            gpd.GeoDataFrame([geojson])
                            .set_geometry("the_geom")
                            .set_crs(4326)
                        )
                        gdf.drop(
                            columns=["geometry", "properties", "type"], inplace=True
                        )
                        gdf["id"], gdf["name"] = id, name

                        if crs_code != None:
                            gdf.to_crs(epsg=crs_code, inplace=True)

                        name_col = gdf.pop("name")
                        gdf.insert(1, "name", name_col)
                        area_gdfs.append(gdf)

            gdf_output = pd.concat(area_gdfs)

    return gdf_output


def get_data_for_gdf_polygons(polygon_gdf, dataset_name_string):
    if dataset_name_string not in list(has_zonal_stats.keys()):
        message = "Bad dataset name string. Choose one of the following: "
        return print(message, list(has_zonal_stats.keys()))
    else:
        dfs = []
        for index_, row in polygon_gdf.iterrows():
            id, name = row.id, row["name"]
            url = str(
                "https://earthmaps.io/"
                + has_zonal_stats[dataset_name_string]
                + str(id)
                + "?format=csv"
            )
            try:
                df = pd.read_csv(url, comment="#")
                df.insert(0, "id", id)
                df.insert(1, "name", name)
                dfs.append(df)
            except:
                print(
                    "Bad request, no "
                    + dataset_name_string
                    + " data for "
                    + str(id)
                    + ": "
                    + name
                    + "...trying next polygon..."
                )

        df_output = pd.concat(dfs)

        return df_output


def cdsapi_timerange_params(start_time, end_time, freq="h"):
    """Generate a dict of time params suitable for CDS API access from start and end times.

    Args:
        start_time (str): starting time for time range in an accepted datetime format
        end_time (str): ending time for time range in an accepted datetime format
        freq (str): frequency for time range

    Returns:
        time_params (dict): dict with keys for time, year, month, and day, representing all discrete time values for which all existing combinations of these values with available data in the API are desired.
    """
    date_range = pd.date_range(start_time, end_time, freq=freq)
    time_params = {
        "time": date_range.strftime("%H:%M").unique().to_list(),
        "year": date_range.strftime("%Y").unique().to_list(),
        "month": date_range.strftime("%m").unique().to_list(),
        "day": date_range.strftime("%d").unique().to_list(),
    }

    return time_params


def unzip(zip_fp, base_fp):
    """Extract contents of a zip file to a destination directory

    Args:
        zip_fp (path-like): path to zip file
        base_fp (pathlib.PosixPath): path to extract the data file to

    Returns:
        base_fp (pathlib.PosixPath): New path to data file in $BASE_DIR
    """
    with ZipFile(zip_fp, "r") as zip_ref:
        zip_info = zip_ref.infolist()
        # iterate across files and change names to have specific hemisphere
        for info in zip_info:
            if ".nc" in info.filename:
                info.filename = base_fp.name
                dest_dir = base_fp.parent
                zip_ref.extract(info, dest_dir)

    return base_fp


def parse_meta_xml_str(meta_xml_str):
    """Parse the DescribeCoverage request to get the XML and restructure the block called "Encoding" to a dict.

    Arguments:
        meta_xml_str (str): string representation of the byte XML response from the WCS DescribeCoverage request

    Returns:
        dim_encodings (dict): lookup table to match data axes or parameters to integer encodings, e.g., '2': 'GFDL-CM3'
    """
    xml_bytes = bytes(bytearray(meta_xml_str, encoding="utf-8"))
    meta_tree = ET.XML(xml_bytes)
    encoding_el = meta_tree.findall(".//Encoding")[0]

    dim_encodings = {}
    for dim in encoding_el.iter():
        if dim.text.startswith("{") and dim.text.endswith("}"):
            encoding_di = eval(dim.text)
            for key, value in encoding_di.items():
                if isinstance(value, dict):
                    dim_encodings[key] = {int(k): v for k, v in value.items()}
                else:
                    dim_encodings[dim.tag] = {int(k): v for k, v in encoding_di.items()}

    return dim_encodings


def assign_coordinate_labels_to_dataset(decode_di, ds):
    """Assign the coordinate labels for a dataset from a dictionary of values

    Args:
        decode_di (dict): a nested dictionary with keys for the coordinate dimension names and associated integer value-coordinate label mappings
        ds (xarray.Dataset): a dataset accessed via Rasdaman which has the integer encodings for the coordinates

    Returns:
        ds (xarra.Dataset): the input dataset with coordinate labels applied
    """
    for k in decode_di.keys():
        try:
            new_coords = [int(decode_di[k][i]) for i in ds[k].values]
        except ValueError:
            new_coords = [decode_di[k][i] for i in ds[k].values]
        ds = ds.assign({k: new_coords})

    return ds
