import os
import numpy as np
import geopandas as gpd
import folium
import branca
from folium.plugins import HeatMap,MarkerCluster


def make_map(geodf,hospitals,output_path,output_name):
	""" Creating map of estimated time arrival to nearest hospital 
	and location of hospitals
	"""

	# Get centroid of country
	centroids = geodf.to_crs(epsg=4326).unary_union.centroid
	lat,lon = centroids.x,centroids.y

	# Get location of hospitals
	hospitals['lon'] = hospitals.geometry.apply(lambda z : z.x)
	hospitals['lat'] = hospitals.geometry.apply(lambda z : z.y)
	locationlist = hospitals[['lat', 'lon']].values.tolist()

	# Longitude/Latitude and Qty of interest columns names
	lat_name = 'center_lat'
	lon_name = 'center_lon'
	qty_interest = 't_hospital'

	# Serie to plot as heatmap
	serie = geodf[qty_interest]

	# Heatmap hyperparameters
	max_heatmap_value = 2
	radius = 5
	blur = 1
	min_opacity = 0.1
	max_zoom = 6

	# Heatmap colorscale
	n_gradient_steps = 5
	colorscale = branca.colormap.linear.viridis.scale(0, 1)
	color_gradient = {x: colorscale(x) for x in np.linspace(0, 1, n_gradient_steps)}

	# Legend colorscale != from heatmap colorscale (heatmaps uses [0, 1] range)
	legend_colorscale = branca.colormap.linear.viridis.scale(serie.min(), max_heatmap_value)
	legend_colorscale.caption = 'Traffic time to closest hospital (h)'

	# Heatmap args
	heatmap_kwargs = {'data': geodf[[lat_name, lon_name, qty_interest]].values.tolist(),
	              'name': serie.name,
	              'min_opacity': min_opacity,
	              'max_zoom': max_zoom,
	              'max_val': max_heatmap_value,
	              'radius': radius,
	              'blur': blur,
	              'gradient': color_gradient
	             }

	heatmap = HeatMap(**heatmap_kwargs)

	m = folium.Map(
	location=[lon,lat],
	tiles='cartodbpositron',
	zoom_start=6.5
	)

	marker_cluster = MarkerCluster().add_to(m)

	for point in range(0, len(locationlist)):
	    folium.Marker(locationlist[point], popup='Hospital', icon=\
	                  folium.Icon(color='red', icon_color='white', icon='ambulance', angle=0, prefix='fa')).add_to(marker_cluster)

	heatmap.add_to(m)

	m.add_child(legend_colorscale)
	m.save(os.path.join(output_path,'Viz_%s.html'%output_name))
	
	return 

