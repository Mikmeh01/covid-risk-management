# Covid-19 Risk Management Data Analysis

Geographic Data Analysis for Covid-19 Risk Management

The purpose of this project is to help policymakers quickly identify areas with poor access to hospitals. This information could help them quickly deploy temporary hospitals (as it was done in France) to halt the spread of the Coronavirus.

## Getting Started

Setup a configuration json file to suit the geodataframe you wish to generate, for example :

```json
{
  "MAPBOX_API_KEY": "your.personnal.key",
  "country_name": "Morocco",
  "window_size": 500
}
```

and then run from `src` directory
```bash
$ python make_geodataframe.py --config=path_to_config --o=output_name
```

Here is an example of interactive map for Tunisia that can be generated [link](https://rawcdn.githack.com/Mikmeh01/covid-risk-management/d1452b1c3e63f90215ca4be850747224e3877a4c/chloropeth_TUN.html)
## Installation

_Requirements file_

## References

_Inspired from this [work](https://github.com/datapartnership/covid19/blob/master/accessibility-Spain.ipynb)_

Datasets:
- Hospitals: OpenStreetMap or Harvard Sub-Saharan Public Hospitals Geo-coded database [link](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/JTL9VY)
- Population: [WorldPop Database](https://www.worldpop.org/)
- Time to Nearest Hospital: [MAPBOX Routing API](https://www.mapbox.com/)

## Vizualisation

To get a grasp of estimated time arrival to hospitals and their location, choose the country and run the "make_viz" notebook and choose the map that suits best your work

<p align="center">
<img src="https://github.com/Mikmeh01/covid-risk-management/blob/master/Viz_Tunisia.png" width="500"/>
</p>
 
