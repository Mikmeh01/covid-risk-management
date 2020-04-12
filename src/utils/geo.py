import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.windows import Window
from matplotlib import pyplot
from pyproj import Transformer
import shapely
from shapely.geometry import point


def rasterio_to_windows_gdf(map_file, window_size):
    # Browsing the raster file, cutting it into squares of size #window
    # and computing bounds, population and number of null values
    df = pd.DataFrame()
    with rasterio.open(map_file) as src:
        for left_x in np.arange(0, src.width, window_size):
            for top_y in np.arange(0, src.height, window_size):
                out = get_pop(map_file, left_x, top_y, window_size, plot=False)
                if out != {}:
                    df = df.append([out])
            print("%i/%i\r" % (left_x, src.width), end="")

    # Transform it to geopandas frame where each row corresponds
    # to a location from where we will compute travel time to closest hospital
    df = df[df['tot_pop'] > 0]
    # df = df[df['split'] != 'done']
    print("We have %i regions of size %i, %i with population >0" %
          (len(df), min(df['window']), len(df[df['tot_pop'] > 0])))
    df = gpd.GeoDataFrame(df, crs='epsg:4326',
                          geometry=[point.Point(xy) for xy in zip(df['center_lon'], df['center_lat'])])
    return df


def split(map_file, origin, plot=False):
    """
    Split a window row in 4 parts, and return new rows results
    based on function get_pop
    """
    origins = pd.DataFrame()
    window = int(origin.window / 2)
    for left_x in np.arange(origin.left_x, origin.right_x, window):
        for top_y in np.arange(origin.top_y, origin.bottom_y, window):
            out = get_pop(map_file, left_x, top_y, window, plot=plot)
            if out != {}:
                origins = origins.append([out])
    return origins


def n_closest_geodetic(destinations, origins, n_keep, verbose=False):
    """
    Given a list of origins and destinations, return the "keep" number
    of destinations that are closest geodetically to each origin.

    Input: destinations,origins <Geopandas>
    Output: destinations filtered <Geopandas>
    """
    filtered = gpd.GeoDataFrame()
    if verbose:
        i = 0
        l = len(origins.index)
    for index in origins.index:
        if verbose:
            i = i + 1
            print("Doing %i of %i\r" % (i, l), end="")
        distances = destinations.distance(origins.loc[index].geometry)
        if len(distances) < n_keep:
            n_keep = len(distances)
        # query indices
        indices = np.argsort(distances.values)[:n_keep]
        # destination indices
        filtered = filtered.append(destinations.iloc[indices])
    if verbose:
        print('done')
    return remove_duplicated_geom(filtered)


def remove_duplicated_geom(gdf):
    """
    Given a GeoDataFrame, remove duplicated geometries
    """
    gdf["geometry"] = gdf["geometry"].apply(lambda geom: geom.wkb)
    gdf = gdf.drop_duplicates(["geometry"])
    gdf.loc[gdf.index, "geometry"] = gdf["geometry"].apply(lambda geom: shapely.wkb.loads(geom))
    return gdf


def get_pop(map_file, left_x, top_y, window, plot=False):
    """
    get_pop(raster filename,left_x,top_y,window,plot=False)

    Given a raster file, and row,cols ranges,
    return the lonlat of the ranges, nancount, and the nunsum

    Optionally plot the raster window [False]
    """
    right_x, bottom_y = left_x + window, top_y + window
    with rasterio.open(map_file) as src:
        left_lon, top_lat = src.xy(top_y, left_x)
        right_lon, bottom_lat = src.xy(bottom_y, right_x)
        center_lon, center_lat = (right_lon + left_lon) / 2., (top_lat + bottom_lat) / 2.
        # Window(col_off, row_off, width, height)
        w = src.read(1, window=Window(left_x, top_y, window, window))
        w = np.where(w == -99999, 0, w)

        if plot:
            pyplot.imshow(w, cmap='pink')
            pyplot.show()
        nancount = np.count_nonzero(~np.isnan(w))
        count = np.size(w)
        tot_pop = np.nansum(w)
    if count == 0:
        return {}  # Out of bounds
    if tot_pop == 0 or window < 1:  # Mark the window to furhter split.
        split = False
    else:
        split = True

    out = {'window': window,
           'left_x': left_x,
           'right_x': right_x,
           'top_y': top_y,
           'bottom_y': bottom_y,
           'left_lon': left_lon,
           'top_lat': top_lat,
           'right_lon': right_lon,
           'bottom_lat': bottom_lat,
           'center_lon': center_lon,
           'center_lat': center_lat,
           'count': count,
           'nancount': nancount,
           'tot_pop': tot_pop,
           'split': split}
    return out


def convert_crs_shap(lat, long, epsg):
    """
    convert_crs_shap2(point,epsg_ini,epsg_final)
    Given a shapely Point, change the projection of the Point
    based on an initial epsg and a final one
    """
    transformer = Transformer.from_crs("epsg:%s" % epsg, "epsg:4326")
    y, x = transformer.transform(lat, long)
    return [str(x), str(y)]


def convert_crs_gdf(gdf, epsg_ini, epsg_final):
    """
    convert_crs_gdf(gdf,epsg_ini,epsg_final)

    Change the crs of the GeoDataFrame gdf given an initial and final epsg

    """
    gdf_bis = gdf.copy()
    gdf_bis.geometry = gdf_bis.geometry.apply(lambda x: convert_crs_shap(x, epsg_ini, epsg_final))
    gdf_bis.crs = {'init': 'epsg=%s' % epsg_final}
    return gdf_bis
