import os
import io
import zipfile
import urllib
import requests
import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import CRS
from shapely.geometry import point


def setup_country_directories(country_name):
    # TODO : factorize this function

    # Load countries dataframe
    country_csv = pd.read_csv('../data/wbccodes2014.csv')

    # Get country isocode and build paths
    country_ISO = country_csv.set_index('country_name').loc[country_name, 'country']
    output_path = os.path.join(country_ISO, 'output')
    pop_folder = os.path.join(country_ISO, 'Data Pop')

    # Build country directory
    if not os.path.exists(country_ISO):
        os.makedirs(country_ISO)

    # Build output subdirectory
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Build population data subdirectory
    if not os.path.exists(pop_folder):
        os.makedirs(pop_folder)
    map_file = os.path.join(pop_folder, '%s_ppp_2019.tif' % country_name)

    # Downloading the raster file for population unless it's already downloaded
    if not os.path.isfile(map_file):
        print('Beginning file download with urllib2...')
        url = 'ftp://ftp.worldpop.org.uk/GIS/Population/Global_2000_2020/2019/%s/%s_ppp_2019.tif' % (country_ISO, country_ISO)
        urllib.request.urlretrieve(url, map_file)

    # Build world shape data subdirectory
    world_shp_path = '../data/World_shp'
    if not os.path.exists(world_shp_path):
        os.makedirs(world_shp_path)
        # Downloading and extracting file
        url_world_shp = 'https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/50m/cultural/ne_50m_admin_0_countries.zip'
        r = requests.get(url_world_shp, stream=True)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(world_shp_path)

    world_shp = gpd.read_file(os.path.join(world_shp_path, 'ne_50m_admin_0_countries.shp'))
    country_shp = world_shp[world_shp.ADM0_A3 == country_ISO.upper()]

    country_centroid = country_shp.unary_union.centroid
    lat, lon = country_centroid.bounds[1], country_centroid.bounds[0]
    # formula below based on :https://gis.stackexchange.com/a/190209/80697
    epsg = int(32700 - np.round((45 + lat) / 90,0) * 100 + np.round((183 + lon) / 6, 0))

    # Build hospital data subdirectory
    hospitals_path = os.path.join(country_ISO, 'Hospitals')
    hospital_shp_path = os.path.join(hospitals_path, '%s.shp' % country_name)

    if not os.path.exists(hospitals_path):
        os.makedirs(hospitals_path)

    if not os.path.exists(hospital_shp_path):
        if country_csv.set_index('country_name').loc[country_name, 'wbregionname'] == 'Sub-Saharan Africa':
            # Downloading and extracting file
            url_hospital = 'https://springernature.figshare.com/ndownloader/files/14379593'
            hospitals_ssa = os.path.join(hospitals_path, 'hospitals.xlsx')
            urllib.request.urlretrieve(url_hospital, hospitals_ssa)
            hospitals_ini = pd.read_excel(hospitals_ssa)
            hospitals_ini = hospitals_ini[hospitals_ini.Country == country_name]
            diff_health_name = 'hospital', 'hôpital', 'hospitalier', 'clinic', 'hospitais'

            hospitals_ini['Facility type lower'] = hospitals_ini['Facility type'].str.lower()
            hospitals_ini = hospitals_ini[hospitals_ini['Facility type lower'].str.contains('|'.join(diff_health_name))]
            geometries_hosp = [point.Point(hospitals_ini.loc[index, 'Lat'], hospitals_ini.loc[index, 'Long']) for index in hospitals_ini.index]
            hosp_temp = pd.DataFrame({'geometry': geometries_hosp})
            hospitals = gpd.GeoDataFrame(hosp_temp, crs=CRS('epsg:4326'), geometry='geometry')
            print('Number of hospitals/clinics :', len(hospitals))

        else:
            # Downloading and extracting file
            url_hospital = 'https://healthsites.io/data/shapefiles/%s.zip' % country_name
            r = requests.get(url_hospital, stream=True)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall(hospitals_path)
            hospital_shp_path = os.path.join(hospitals_path, '%s-node.shp' % country_name)
            hospitals = gpd.read_file(hospital_shp_path)

            hospitals = hospitals[(hospitals.healthcare.isin(['clinic', 'hospital'])) | (hospitals.amenity.isin(['clinic', 'hospital']))]
            print('Number of hospitals/clinics :', len(hospitals))
        hospitals.to_file(os.path.join(output_path, 'hospitals.shp'))

    return output_path, map_file, country_shp, epsg
