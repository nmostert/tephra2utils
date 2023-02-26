## Generate UTM Grid

This script generates a regular grid of UTM coordinates given two opposite corners of a rectangle on a UTM grid and a regular spacing distance. It can be used to create a grid of UTM coordinates for various applications, such as in geospatial analysis and mapping.

### Usage

The script takes the following arguments:

* `min_easting`: The minimum easting value of the rectangle.
* `max_easting`: The maximum easting value of the rectangle.
* `min_northing`: The minimum northing value of the rectangle.
* `max_northing`: The maximum northing value of the rectangle.
* `spacing`: The regular spacing distance between points in the grid.
* `output_file`: The name of the output file. If not specified, it will default to "output.txt".

To run the script, use the following command:

```
python generate_utm_grid.py min_easting max_easting min_northing max_northing spacing [output_file]
```

### Example

To generate a grid with a spacing of 1000 units and save it to a file named "`utm_grid.txt`", with the minimum easting and northing values of 0 and maximum values of 10000, the following command can be used:

```
python generate_utm_grid.py 0 10000 0 10000 1000 utm_grid.txt
```

### Notes

For now, this utility assumes that all points are in the same UTM zone. If the points span multiple UTM zones, it will break.

## Regular Grid Map Visualisation 

![Example](https://github.com/nmostert/tephra2utils/blob/master/test.html "Example Grid Visualisation")

The Python script `plot_reg_grid.py` takes in a CSV file of UTM coordinates and plots them on a world map using the folium package. 

This script requires the following Python packages to be installed:

* `argparse`
* `numpy`
* `pandas`
* `folium`
* `utm`

### Usage

To run the script, use the following command in the terminal:

```
python regular_grid_plotter.py input_file utm_zone output_file
```

where

```
input_file: the path to the input CSV file containing the UTM coordinates
utm_zone: the UTM zone number and letter (e.g. "10N") for the coordinates
output_file: the path to the output HTML file for the plotted coordinates
```

The CSV file should have the following format:

```
# Northing Easting Elevation
4000000 500000 0
4000000 500100 0
4000000 500200 0
...
```
### Output

The script will generate an HTML file containing the plotted UTM coordinates on a world map centered at the mean latitude and longitude of the input coordinates. Each coordinate will be represented by a red circle marker on the map.
The output can be opened in a browser.

### Example

Here is an example command to run the script:

```
python regular_grid_plotter.py input.csv 10N output.html
```

This will read in the UTM coordinates from input.csv in UTM zone 10N, and generate an HTML file output.html containing the plotted coordinates on a world map.

### Notes

For now, this utility assumes that all points are in the same UTM zone. If the points span multiple UTM zones, it will break.
