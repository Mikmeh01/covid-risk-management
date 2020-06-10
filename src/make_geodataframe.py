import os
import warnings
from absl import app, flags
import json
import utils
import geopandas as gpd


warnings.filterwarnings("ignore")
FLAGS = flags.FLAGS


def main(argv):
    del argv

    # Load config file
    with open(FLAGS.config, 'r') as f:
        config = json.load(f)

    # Setup working directories
    foo = utils.setup_country_directories(config['country_name'])
    output_path, map_file, country_shp, epsg = foo

    # Get country and hospitals geodataframe
    gdf = utils.rasterio_to_windows_gdf(map_file=map_file,
                                        window_size=config['window_size'])
    hospitals = gpd.read_file(os.path.join(output_path, 'hospitals.shp'))

    # Register dataframes on same reference
    gdf = gdf.reset_index(drop=True)
    hospitals = hospitals.reset_index(drop=True)
    gdf = gdf.to_crs(epsg=epsg)
    hospitals_crs = hospitals.to_crs(epsg=epsg)

    # Compute time travel from each cell to nearest hospital
    foo = utils.mapbox_matrix_API(origins=gdf,
                                  destinations=hospitals_crs,
                                  token=config['MAPBOX_API_KEY'],
                                  epsg=epsg,
                                  name='hospital',
                                  n_keep=2)

    # Dump geodataframe
    gdf['t_hospital'] = foo['t_hospital']
    gdf['so_hospital'] = foo['so_hospital']
    # gpd.sjoin(gdf, country_shp, op='within')[gdf.columns].to_file(os.path.join(output_path, 'origins.shp'))
    gdf.to_file(os.path.join(output_path, FLAGS.o))

    # Make and export map
    utils.make_map(gdf,hospitals,output_path,FLAGS.o)


if __name__ == '__main__':
    flags.DEFINE_string('config', './config.json', "configuration file to load")
    flags.DEFINE_string('o', 'output.shp', "output file name")
    app.run(main)
    raise NotImplementedError
