# Covid-19 Risk Management Data Analysis

Geographic Data Analysis for Covid-19 Risk Management

The purpose of this project is to help policymakers quickly identify areas with poor access to hospitals. This information could help them quickly deploy temporary hospitals (as it was done in France) to halt the spread of the Coronavirus.

## Getting Started

_provide very short code sample and result to give a grasp of what the project is about and what's achievable with the code (ideally some quick map visualization)_

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

## Installation

_Requirements file_

## References

_Inspired from this [work](https://github.com/datapartnership/covid19/blob/master/accessibility-Spain.ipynb)_

Datasets:
- Hospitals: OpenStreetMap or Harvard Sub-Saharan Public Hospitals Geo-coded database [link](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/JTL9VY)
- Population: [WorldPop Database](https://www.worldpop.org/)
- Time to Nearest Hospital: [MAPBOX Routing API](https://www.mapbox.com/)
