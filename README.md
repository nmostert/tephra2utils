# Tephra2 Utilities

This is a collection of utilities for Tephra2 simulations. At present it contains four scripts:

* `generate_utm_grid.py` generates a regularly spaced grid file for Tephra2 given UTM coordinates.
* `plot_reg_grid.py` generates an html file showing the grid spacing.
* `tephra2_run_generator.py` generates a csv file containing configurations for a batch Tephra2 simulation run with parameters generated using user-specified sample functions.
* `tephra2_runner.sh` executes a batch of Tephra2 runs using the output from `tephra2_run_generator.py`

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

![plot_example](https://user-images.githubusercontent.com/34159030/221457523-967d75c3-dcab-4df2-9414-be54b6219e09.png)

The Python script `plot_reg_grid.py` takes in a CSV file of UTM coordinates and plots them on a world map using the folium package. 

This script requires the following Python packages to be installed:

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

## Tephra2 Batch Simulation Configuration Generator

This Python script generates configurations for a Tephra2 simulation run. It takes an input file and generates a number of configurations (specified by the user) using the parameters in the input file.
Prerequisites

This script requires the following packages to be installed:

* NumPy
* Pandas

### Usage

The script can be run using the following command:

```
python tephra2_run_generator.py input_file runs output_file
```

where `input_file` is the name of the input file, `runs` is the number of configurations to generate, and `output_file` is the name of the output file to which the generated configurations will be written.

The input file should contain lines of the format:

```
<PARAMETER_NAME> <fixed_value>
```

for a parameter that will remain constant for all runs, or

```
<PARAMETER_NAME> {<sample_function_name>} [<param_1>, <param_2>, ...]
```

where `<sample_function_name>` is a function defined in the script that generates a value for `<PARAMETER_NAME>`.

It is also possible to use the value of other parameters to calculate dependent parameters. To do this, use the pipe symbol (`|`) to reference the parameter. 
For example:

```
<FIRST_PARAMETER> {<sample_function_name>} [<param_1>, <param_2>, |<OTHER_PARAMETER>|]
<OTHER_PARAMETER> <fixed_value>
```

Here, `FIRST_PARAMETER` is calculated internally using the call

```
<sample_function_name>(<param_1>, <param_2>, <OTHER_PARAMETER>)
```

**NOTE: This functionality is limited, and will break if faced with cyclical or nested dependencies.**


The output file will contain a Pandas DataFrame with the generated configurations, of the format:

```
run,<param1>,<param2>,<param3>,...,<paramN>
0,<value1>,<value2>,<value3>,...,<valueN>
1,<value1>,<value2>,<value3>,...,<valueN>
...
```

This can be passed directly into `tephra2_batch_runner.sh` for batch simulation runs.

### Sampling Functions

For now, the following functions are defined in the script:

* `unif(a, b)`: Generates a random value between a and b using a uniform distribution.

* `log_unif(a, b)`: Generates a random value between a and b using a logarithmic uniform distribution. 

* `trunc_lognorm(mean, std, max_val)`: Generates a random value using a lognormal distribution around `mean` and `std`, truncated at `max_val`. 

More will be added in time. Feel free to suggest additional functions.

## Tephra2 Batch Simulation Script 

This is a command line utility to run the Tephra2 volcanic ash dispersion model for multiple parameter sets specified in a CSV file.

### Usage

```
tephra2_batch_runner.sh [-h] [-t TEHRA2_PATH] [-p PARAMETER_FILE] [-g GRID_FILE] [-w WIND_FILE] [-o OUTPUT_FILE_PREFIX]

    -h: Display help message and exit.
    -t TEHRA2_PATH: Path to the Tephra2 executable. Default is /usr/local/tephra2/tephra2.
    -p PARAMETER_FILE: Path to the CSV file containing the parameter sets. Required.
    -g GRID_FILE: Path to the grid file containing the UTM coordinates of the study area. Required.
    -w WIND_FILE: Path to the wind file containing wind direction and speed data. Required.
    -o OUTPUT_FILE_PREFIX: Prefix for the output files. Default is tephra2_output.
```

### Input

#### Parameter file

The parameter file should be a CSV file with the following format:

```
run,<param1>,<param2>,<param3>,...,<paramN>
0,<value1>,<value2>,<value3>,...,<valueN>
1,<value1>,<value2>,<value3>,...,<valueN>
...
```

The first row should contain the names of the parameters. The first column should contain the string run, followed by the parameter names.

The subsequent rows should contain the parameter values for each run, with the first column containing the run number (starting from 0).

This file can be generated using the python script `tephra2_run_generator.py`. 

#### Grid file

The grid file should be a text file with UTM coordinates of the study area, in the following format:

```
<easting1> <northing1>
<easting2> <northing2>
...
```

#### Wind file

The wind file should be a text file with wind direction and speed data, in the following format:

```
<direction1> <speed1>
<direction2> <speed2>
...
```

#### Output

The utility generates one output file per run, with the name specified by the -o option, appended with `_run<run number>.txt`.

Each output file contains the Tephra2 output for the corresponding run, in text format.

### Example usage

```
tephra2_runner.sh -t /usr/local/tephra2/tephra2 -p parameter_file.csv -g grid_file.txt -w wind_file.txt -o tephra2_output
```

This runs Tephra2 with the parameters specified in `parameter_file.csv`, using the grid file `grid_file.txt` and wind file `wind_file.txt`, and saves the output in files named `tephra2_output_run0.txt`, `tephra2_output_run1.txt`, etc.


## NetCDF to Tephra2 Converter

This script is a utility for converting wind data in a netCDF file to Tephra2 format.

### Usage

```
usage: netcdf_to_tephra2.py [-h] [-a] netcdf_file output_file date [date ...]

Utility for converting wind data in a netcdf file to Tephra2 format

positional arguments:
  netcdf_file        Path to the netcdf file containing wind data
  output_file        Path/prefix for the output file/files
  date               Date(s) to extract in yyyy-mm-dd format. Can be a single
                     date, a date range (in the form of start_date:end_date), a
                     list of dates separated by spaces, or a file containing a
                     date on each line.

optional arguments:
  -h, --help         show this help message and exit
  -a, --aggregate    If set, all files in the date range will be aggregated
                     using the mean to a single output file.

The script takes the following arguments:

    netcdf_file: Path to the netCDF file containing wind data
    output_file: Path/prefix for the output file/files
    date: Date(s) to extract in yyyy-mm-dd format. Can be a single date, a date range (in the form of start_date:end_date), a list of dates separated by spaces, or a file containing a date on each line.
    -a, --aggregate: If set, all files in the date range will be aggregated using the mean to a single output file.
```

To use the script, simply run it with the required arguments:

```
python netcdf_to_tephra2.py <netcdf_file> <output_file> <date>
```

For example, to convert wind data for January 1st, 2022 to Tephra2 format, you would run:

```
python netcdf_to_tephra2.py /path/to/netcdf/file.nc /path/to/output/file 2022-01-01
```

You can also specify a date range using the `start_date:end_date` syntax:

```
python netcdf_to_tephra2.py /path/to/netcdf/file.nc /path/to/output/file 2022-01-01:2022-01-10
```

To specify multiple dates, simply separate them with spaces:

```
python netcdf_to_tephra2.py /path/to/netcdf/file.nc /path/to/output/file 2022-01-01 2022-01-02 2022-01-03
```

You can also specify a file containing a list of dates, with one date per line:

```
python netcdf_to_tephra2.py /path/to/netcdf/file.nc /path/to/output/file /path/to/dates.txt
```

Finally, if you want to aggregate all the files in a date range into a single file by calculating the mean, use the -a or --aggregate flag:

```
python netcdf_to_tephra2.py /path/to/netcdf/file.nc /path/to/output/file 2022-01-01:2022-01-10 -a
```

## Tephra2 Multiphase Config Generator

This script generates Tephra2 input configurations for a multiphase eruption scenario.

### Usage
```
usage: tephra2_multiphase_generator.py [-h] [-o OUTPUT] [-q | -v | -d]
                                       config_file phase_config_dir wind_file start_date

Generate Tephra2 input files for multiple eruption phases.

positional arguments:
  config_file           path to the multiphase configuration file. The file should have
                        columns for phase type,
                        duration, following quiescence, and description.
  phase_config_dir      path to the directory containing the config templates for the
                        eruption types specified in the "Type" column of the
                        config_file. The file should have columns for phase type,
                        duration, following quiescence, and description.
  wind_file             path to the .net pdf wind file from which to extract wind files
                        for each eruption.
  start_date            starting date in YYYY-MM-DD format. This is the date at which
                        phase 0 in the eruption begins.
                        The dates for subsequent eruptions are calculated based on the
                        total durations and quiescences of preceding eruptions.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        output directory path. If not specified, the output will be
                        written to the current working directory.
  -q, --quiet           Suppress all output
  -v, --verbose         Enable verbose output
  -d, --debug           Enable debug output
```

#### Multiphase configuration file
The phases of the eruption are described by the user using the `<config_file>` argument, which is the path to a .csv file. Each line descibes a single phase of the eruption sequence. The columns of the file are expected to be as follows:

- `Phase Type`: The eruption style of the phase. This text must correspond exactly with the filename (without extension) of one of the phase configuration files in the `<phase_config_dir>` directory.
- `Duration`: The duration (in days) of the phase.
- `Following Quiescence`: The duration (in days) of the quiescent period before the next phase.
- `Description`: An optional column containing descriptive text.

Here is an example of a valid phase configuration file contents:

Phase Type | Phase Duration| Following Quiescence|   Description
---|---|---|---
IntExp|42|2|Intermittent Explosions, Dome destroyed
Eff+Exp|53|0|Intermittent explosions and dome collapses
PlinianE|1|2|Plinian Eruption
MajorE|1|0|SubPlinian Eruption

#### Phase Types

Each phase type must have a Tephra2 configuration file. By default some example phase configs are supported. 

Phases can be categorised into two distinct groups, namely "single-bang" and "multi-bang"

- "single-bang" phases consist of a single large eruptive event that can be stretched over multiple days. 
- "multi-bang" phases consist of multiple smaller eruptions that all form part of a larger eruptive phase. 

**"single-bang"** events can be described using a single generic Tephra2 configuration file, using the sampling syntax described [here](#parameter-file).






