import numpy as np
import rasterio
from rasterio.windows import Window
from matplotlib import pyplot
from pyproj import Proj, transform
from shapely.geometry import Point
import geopandas as gpd
import shapely

def remove_duplicated_geom(gdf):
    """
    Given a GeoDataFrame, remove duplicated geometries
    """
    gdf["geometry"] = gdf["geometry"].apply(lambda geom: geom.wkb)
    gdf = gdf.drop_duplicates(["geometry"])
    gdf["geometry"] = gdf["geometry"].apply(lambda geom: shapely.wkb.loads(geom))
    return gdf

def get_pop(map_file,left_x,top_y,window,plot=False):
    """
    get_pop(raster filename,left_x,top_y,window,plot=False)
    
    Given a raster file, and row,cols ranges,
    return the lonlat of the ranges, nancount, and the nunsum
    
    Optionally plot the raster window [False]
    """
    right_x,bottom_y = left_x + window, top_y + window
    with rasterio.open(map_file) as src:
        left_lon, top_lat = src.xy(top_y,left_x )
        right_lon, bottom_lat = src.xy(bottom_y, right_x )
        center_lon , center_lat = (right_lon + left_lon)/2., (top_lat+bottom_lat)/2.
                             #Window(col_off, row_off, width, height)
        w = src.read(1, window=Window(left_x, top_y, window, window))
        w = np.where(w==-99999, 0, w) 
        
        if plot:
            pyplot.imshow(w, cmap='pink')
            pyplot.show()
        nancount=np.count_nonzero(~np.isnan(w))
        count = np.size(w)
        tot_pop=np.nansum(w)
    if count == 0:
        return {} #Out of bounds
    if tot_pop == 0 or window < 1: #Mark the window to furhter split.
        split=False
    else:
        split=True
    out={'window':window,
         'left_x':left_x,
         'right_x':right_x,
         'top_y':top_y,
         'bottom_y':bottom_y,
         'left_lon':left_lon, 
         'top_lat':top_lat, 
         'right_lon':right_lon,
         'bottom_lat':bottom_lat,
         'center_lon':center_lon , 
         'center_lat':center_lat,
         'count': count,
         'nancount':nancount,
         'tot_pop':tot_pop,
         'split': split}
    return out
    
def convert_crs_shap(long,lat,epsg):
    original = Proj(init='EPSG:%s'%epsg) # EPSG:4326 in your case
    destination = Proj(init='EPSG:4326') # your new EPSG
    x,y = transform(original, destination,long,lat)
    return [str(x),str(y)]

def convert_crs_shap2(point,epsg_ini,epsg_final):
    """
    convert_crs_shap2(point,epsg_ini,epsg_final)
    Given a shapely Point, change the projection of the Point 
    based on an initial epsg and a final one
    """
    original = Proj(init='EPSG:%s'%epsg_ini) # EPSG:4326 in your case
    destination = Proj(init='EPSG:%s'%epsg_final) # your new EPSG
    long,lat = point.x, point.y
    x,y = transform(original, destination,long,lat)
    return Point(x,y)

def convert_crs_gdf(gdf,epsg_ini,epsg_final):
    """
    convert_crs_gdf(gdf,epsg_ini,epsg_final)

    Change the crs of the GeoDataFrame gdf given an initial and final epsg

    """
    gdf_bis = gdf.copy()
    gdf_bis.geometry = gdf_bis.geometry.apply(lambda x: convert_crs_shap2(x,epsg_ini,epsg_final))
    gdf_bis.crs = {'init':'epsg=%s'%epsg_final}
    return gdf_bis