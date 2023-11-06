import requests
import json
import pandas as pd
import geopandas as gpd
import shapely



valid_areas = [
    'communities',
    'hucs',
    'protected_areas',
    'corporations,',
    'climate_divisions',
    'fire_zones',
    'ethnolinguistic_regions',
    'boroughs',
    'census_areas',
    'game_management_units',
    'first_nations'
]

has_zonal_stats = {
    'indicators':'indicators/base/area/',
    'beetles':'beetles/area/',
    'elevation':'elevation/area/',
    'flammability':'alfresco/flammability/area/',
    'veg_type':'alfresco/veg_type/area/',
    'temperature':'temperature/area/',
    'precipitation':'precipitation/area/',
    'temperature_and_precipitation':'taspr/area/',
}


def get_area_gdf_by_category(area_category_string, crs_code=None):

    if (crs_code != None) & (type(crs_code) != int):
        return print("CRS code must be EPSG as integer.")

    if area_category_string not in valid_areas:
        message = "Bad area category string. Choose one of the following: "
        return print(message, valid_areas)
    else:
        with requests.Session() as s:
            area_names_response = s.get('https://earthmaps.io/places/' + area_category_string)
            area_names_json_list = area_names_response.json()

        if area_names_response.status_code != 200:
            return "bad request"
        else:
            area_gdfs = []
            for area in area_names_json_list:
                id, name = area['id'], area['name']
                with requests.Session() as s:
                    area_poly_response = s.get(str('https://earthmaps.io/boundary/area/' + str(id)))
                    if area_poly_response.status_code != 200:
                            print("bad request")
                    else:
                        geojson = area_poly_response.json()
                        geojson['the_geom'] = shapely.from_geojson(json.dumps(geojson))
                        gdf = gpd.GeoDataFrame([geojson]).set_geometry('the_geom').set_crs(4326)
                        gdf.drop(columns=['geometry', 'properties', 'type'], inplace=True)
                        gdf['id'], gdf['name'] = id, name

                        if crs_code != None:
                            gdf.to_crs(epsg = crs_code, inplace=True)

                        name_col = gdf.pop('name')
                        gdf.insert(1, 'name', name_col)
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
            id, name = row.id, row['name']
            url = str('https://earthmaps.io/' + has_zonal_stats[dataset_name_string] + str(id) + '?format=csv')
            try:
                df = pd.read_csv(url, comment="#")
                df.insert(0, "id", id)
                df.insert(1, "name", name)
                dfs.append(df)
            except:
                print("Bad request, no " + dataset_name_string + " data for " + str(id) + ": " + name + "...trying next polygon...")               
            
        df_output = pd.concat(dfs)

        return df_output
