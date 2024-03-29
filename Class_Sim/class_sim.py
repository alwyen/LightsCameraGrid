import argparse
from numpy import save
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon, box
import os
import time
import sys
import random
import glob

os_sep = os.sep
cwd = list(os.getcwd().split(os_sep))
STIMA_scripts_dir = os_sep.join(cwd[:len(cwd)-1])
STIMA_dir = os_sep.join(cwd[:len(cwd)-3])
BRF_Analysis_dir = os.path.join(STIMA_scripts_dir, 'BRF_Analysis')

sys.path.insert(1, BRF_Analysis_dir)
import brf_database_analysis_v2

'''
DESCRIPTION: generates random points in a polygon

INPUT:  number              number of random points for a polygon
        polygon
OUTPUT: list_of_points      list of random points in lat long format(?)
'''
def generate_random_spatialpoints(number, polygon):
    #Source: https://gis.stackexchange.com/questions/207731/generating-random-coordinates-in-multipolygon-in-python
    list_of_points = []
    minx, miny, maxx, maxy = polygon.bounds
    counter = 0
    while counter < number:
        x = random.uniform(minx, maxx)
        y = random.uniform(miny, maxy)
        pnt = Point(x,y)
        if polygon.contains(pnt):
            list_of_points.append((x,y))
            counter += 1
    return list_of_points

'''
DESCRIPTION:    creates a new geo dataframe with random points within new polygons with associated BRFs
                saves data frames in new folder

INPUT:  geojson_path    path to geojson file
        boundary_path   path to lat-long box boundaries to narrow down df

OUTPUT: nothing; files are in `folder_name`
'''
def save_new_dfs(folder_name, save_path, geojson_path, boundary_path):
    if not os.path.isdir(save_path):
        os.mkdir(save_path)

    # extracting new scenarios; make multiple gdfs,
    # put into new files; make option to process again or just use from saved file
    boundary_df = pd.read_csv(boundary_path)
    xmin_list = boundary_df.xmin.tolist()
    ymin_list = boundary_df.ymin.tolist()
    xmax_list = boundary_df.xmax.tolist()
    ymax_list = boundary_df.ymax.tolist()

    # assertions
    assert len(xmin_list) == len(ymin_list)
    assert len(ymin_list) == len(xmax_list)
    assert len(xmax_list) == len(ymax_list)

    start_time = time.time()
    gdf = gpd.read_file(geojson_path)
    # print(gdf.crs)
    print(f'Time elapsed for loading file (seconds): {time.time() - start_time}')
    print()

    for i in range(len(xmin_list)):
        # filtering out 
        boundary_box = box(xmin_list[i], ymin_list[i], xmax_list[i], ymax_list[i])
        bounded_gdf = gdf.intersection(boundary_box)
        bounded_gdf = gpd.GeoDataFrame(bounded_gdf[~bounded_gdf.is_empty])
        bounded_gdf = bounded_gdf.rename(columns={0:'geometry'}).set_geometry('geometry')

        # generate save path
        layout_name_path = os.path.join(save_path, folder_name + '_layout_' + str(i))
        bounded_gdf.to_file(layout_name_path)

'''
DESCRIPTION: loads GeoDataFrames from .shp file from save path into a list

INPUT:      save_path       path to all saved folders/.shp files

OUTPUT:     gdf_list        returns list of GeoDataFrames
'''

def load_gdfs(save_path):
    gdf_list = list()
    scenario_list = glob.glob(save_path + '/*/', recursive=True)
    for scenario_path in scenario_list:
        # getting the path of the file for the scenario_path
        dirs = scenario_path.split('/')
        file_name = dirs[len(dirs)-2] + '.shp'
        scenario_path = scenario_path + file_name
        gdf = gpd.read_file(scenario_path)

        # iloc[row, col]
        gdf = gdf.iloc[:, 1:] # iloc --> integer location; removing first column (was FID)
        
        gdf_list.append(gdf)
    
    return gdf_list

'''
DESCRIPTION: takes in a GeoDataFrame and computes the random points of buffered polygons

INPUT:      gdf             GeoDataFrame
            error_amount    location radial error amount in meters

OUTPUT:     gdf             GeoDataFrame with the following columns:
                            geometry | buffer_geometry | random_points
'''

def compute_random_points(gdf, error_amount):
    gdf = gdf.to_crs(epsg=3857)
    gdf['buffer_geometry'] = gdf.buffer(20) # 20 represents the approximate distance from street lights to houses
    gdf['ground_points'] = gdf['buffer_geometry'].apply(lambda row: generate_random_spatialpoints(1, row))
    gdf_copy = gdf.copy()
    print(gdf_copy.head())
    gdf_copy['geometry'] = gdf_copy['ground_points']
    gdf_copy = gdf_copy.drop('ground_points')
    gdf_copy = gdf_copy.drop('buffer_geometry')
    gdf_copy.plot()
    plt.show()

    gdf['circle_geometry'] = gdf['ground_points'].buffer(error_amount)
    gdf['estimated_points'] = gdf['circle_geometry'].apply(lambda row: generate_random_spatialpoints(1, row))
    
    # convert everything back to 4326 (WGS 84)
    gdf['geometry'] = gdf['geometry'].to_crs(crs=4326)
    gdf['buffer_geometry'] = gdf['buffer_geometry'].to_crs(crs=4326)
    gdf['ground_points'] = gdf['ground_points'].to_crs(crs=4326)
    gdf['circle_geometry'] = gdf['circle_geometry'].to_crs(crs=4326)
    gdf['estimated_points'] =gdf['estimated_points'].to_crs(crs=4326)

    gdf.plot('geometry')
    gdf.plot('buffer_geometry')
    gdf.plot('ground_points')
    gdf.plot('circle_geometry')
    gdf.plot('estimated_points')
    plt.show()

    # print(gdf['geometry'])
    # print(gdf['buffer_geometry'])
    # print(gdf['random_points'])
    print(gdf.head())

    # gdf.geometry.plot()
    # gdf.buffer_geometry.plot()


    '''
    TODO:   shapely --> make smaller geojson file to load (and make an option for that)
            print out shapes
            compute centroid of polygons of geometry column (check geopandas df column names)
            (Zeal said something about using `gdf.geometry.centroid` with `.apply`)
            create buffer points from polygon (20m; figure that out)
            geometry columns should be:
                building polygon | centroid of building | then buffer around centroid
            then generate random points inside buffer; result should be:
                building polygon | centroid of building | then buffer around centroid | random point
            need to attach brf label to random point, so create another column with that
            (I think that should be it...?)
            figure out how to plot original buildings + buffer + random points to visualize stuff
    '''

def main(args):
    error_amount = 15

    geojson_path = os.path.join(STIMA_scripts_dir, 'Class_Sim', 'geojson_files', args.geojson_path)
    boundary_path = os.path.join(STIMA_scripts_dir, 'Class_Sim', 'geojson_files', args.boundary_path)

    geojson_temp = list(geojson_path.split(os.sep))
    folder_name = geojson_temp[len(geojson_temp) - 1].split('.')[0]
    save_path = os.path.join(os.getcwd(), folder_name)

    print('Regenerate files? [y]/other')
    user_input = input()
    if user_input == 'y':
        print('Are you sure? This will take some time. [y]/other')
        user_input = input()
        if user_input == 'y':
            save_new_dfs(folder_name, save_path, geojson_path, boundary_path)

    gdf_list = load_gdfs(save_path)

    for gdf in gdf_list:
        compute_random_points(gdf, error_amount)




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-gp', '--geojson_path', required=True, type=str, help='geojson file name; Example: Alaska.geojson')
    parser.add_argument('-bp', '--boundary_path', required=True, type=str, help='boundary csv file name; Example: Alaska_boundaries.csv')
    args = parser.parse_args()
    main(args)