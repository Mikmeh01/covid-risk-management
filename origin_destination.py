import requests
import numpy as np
import random
from closest_hospital import n_closest_geodetic
from utils import convert_crs_shap
import pandas as pd
import geopandas as gpd
import json
import time


def mapbox_matrix_API(origins, destinations,token,epsg,mode=1,name='poi',destination_id_col=False,n_keep=3,do_all=False,verbose=True):
    """
    Given a geopandas set of origins and destinations, return the origins with extra columns
    with the closest destination in minutes given the mode of transportation for each origin.
    
    Also returns the snap distance to the origin (geodetic distance from origin point to closest road)
    Keywords:
    do_all [False]: By default avoid repeating work that has been done.
    
    """
    osrm_server = "https://api.mapbox.com/directions-matrix/v1/mapbox/"
    modes = ['driving-traffic', 'driving', 'cycling', 'walking']
    url = osrm_server+modes[mode]+'/'
    params = "?annotations=distance,duration&access_token="+token

    o_type = 'hospital'
    batch = int(np.floor(24/n_keep))

    if n_keep*batch>25:
        print("limit 25< %i (keep) * %i (batch)"%(n_keep,batch))

    cols=['t_'+o_type,'m_'+o_type,'so_'+o_type]

    #only do empty ones
    if not do_all:
        queued_origins = origins[origins['t_hospital']==-1]
    else:
        queued_origins = origins
    if verbose:
        print("Doing %i"%len(queued_origins))

    for i in np.arange(queued_origins.shape[0]/batch):
   
        print("Doing batch %i, from %i to %i, of %i"
          %(i+1,batch*i,batch*(i+1),queued_origins.shape[0]),end="\r")
        #get origin batch
        o_batch = queued_origins.iloc[int(batch*i):].head(n=batch)


        #to reduce API calls calculate keep only n closest (geodetically) to
        #each origin.
        h_batch = n_closest_geodetic(destinations,o_batch,n_keep)
        
        # Free MAPBOX API doesn't allow to have more than 25 points in origin destination matrix
        if len(h_batch)>25 - int(np.floor(24/n_keep)):
            h_batch = h_batch.loc[random.sample(list(h_batch.index),25 - int(np.floor(24/n_keep))),:]
        h_batch_loc=\
        ";".join([",".join(convert_crs_shap(row.centroid.x, row.centroid.y,epsg)) for row in h_batch['geometry']])

        #create url params of origin batch
        d=\
        ";".join([",".join(convert_crs_shap(row.centroid.x, row.centroid.y,epsg)) for row in o_batch['geometry']])
        d_name = o_batch.index

        trail=".json?destinations="+\
        ';'.join([str(x) for x in np.arange(len(h_batch))])+\
        "&sources="+\
        ';'.join([str(x) for x in np.arange(len(h_batch),len(h_batch)+len(o_batch))])

        fullurl= url+h_batch_loc+";"+d+trail+params

        #print(fullurl)
        response = requests.get(fullurl)
        response.raise_for_status()
        response=json.loads(response.text)
        #print(response)
        response_matrix = response['durations']
        durations = []
        h_min = []
        for origin in np.arange(np.shape(response_matrix)[0]):
            durations+=[min(response_matrix[origin])]
            h_min+=[np.argmin(response_matrix[origin])]
        for i in np.arange(len(durations)):
            queued_origins.loc[[d_name[i]], ['t_'+o_type]]=durations[i]/60./60.
            if destination_id_col != False:
                queued_origins.loc[[d_name[i]], ['m_'+o_type]] = h_batch.iloc[h_min[i]][destination_id_col]
            queued_origins.loc[[d_name[i]], ['so_'+o_type]]=response['sources'][i]['distance']
        time.sleep(0.8)


    print("\n")
    #update the "origins" with the results

    pd.set_option('mode.chained_assignment', None) #'warn'
    origins.loc[queued_origins.index, (cols)] = queued_origins.loc[:,(cols)].copy()
    print("returning")

    return origins
