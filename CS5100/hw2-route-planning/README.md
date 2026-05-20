# Route

The following sections detail some general notes for working with `route`, including setup, and
various dependency requirements.

## Prerequisites

Install the following dependencies, ideally in a virtual environment such as
 [mamba](https://github.com/conda-forge/miniforge#install) (faster) or [miniconda](https://docs.conda.io/en/latest/miniconda.html#linux-installers) (slower), for working with
 [OpenStreetMap](https://www.openstreetmap.org/) (OSM) data, and visualizing maps nicely in the browser.

***Please use python 3.8.***

```bash
# Recommended: use a virtual env (make sure the virtual env is installed on your machine)
mamba create -n route python=3.8
mamba activate route
# Install requirements
pip install -r requirements.txt
```

If you're getting "module not found" errors after downloading all the requirements, try using `python3` instead of `python` on the command line.

## Creating a Custom Map

1. Use `extract.bbbike.org` to select a geographic region.
2. Download a `<name>.pbf` and place it in the `data` directory.

### Adding Custom Landmarks

Landmark files have the following format:

```json
[
  {"landmark": "northeastern_building", "geo": "37.337504,-121.890144"},
  {"landmark": "starbucks", "geo": "37.338223,-121.886577"},
  {"landmark": "philz", "geo": "37.333737, -121.884490"},
  {"landmark": "san_pedro_market", "amenity": "food", "geo": "37.336735, -121.894149"},
  {"landmark": "bus_station","geo": "37.33603785821357, -121.89049954245998"},
  ...
]
```
See `data/stanford-landmarks.json` for an example. You can add your own to `data/custom-landmarks.json`.

To add a landmark, find it on [OpenStreetMap](https://www.openstreetmap.org/) via [nominatim](https://nominatim.openstreetmap.org/) and
copy the `Center Point (lat,lon)` from the `nominatim` webpage
(e.g., [Gates Building](https://nominatim.openstreetmap.org/ui/details.html?osmtype=W&osmid=232841885&class=building),
and set that to be the value of `"geo"`.

## Visualizing the Map

To visualize a particular map, you can use the following:

```bash
python visualization.py  # or "python3 ..." for the following


# You can customize the map and the landmarks
python visualization.py --map-file data/sanjose.pbf --landmark-file data/sanjose-landmarks.json

# Visualize a particular solution path (requires running `grader.py` on question 1b/2b first!)
python visualization.py --path-file path.json
```
