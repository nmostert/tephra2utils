import os
import argparse
import subprocess
from datetime import datetime
from netcdf_wind_extractor import NetCDFWindExtractor
import logging
import time
import sys
import re
import multiprocessing as mp
import h5py
import pandas as pd
import numpy as np
import shutil


def validate_input_files(multiphase_config_file, netcdf_file, grid_file, tephra2_path):
    """
    Validate input files.
    """
    # Check if files exist
    for file_path in [
        multiphase_config_file,
        netcdf_file,
        grid_file,
    ]:
        if not os.path.exists(file_path):
            raise ValueError(f"File {file_path} not found.")

    # Check if files are valid
    if not multiphase_config_file.endswith(".csv"):
        raise ValueError("Multiphase config file must be a CSV file.")
    if not netcdf_file.endswith(".nc"):
        raise ValueError("NetCDF file must be a NetCDF file.")
    if not grid_file.endswith(".csv"):
        raise ValueError("Grid file must be a CSV file.")
    if not os.access(tephra2_path, os.X_OK):
        raise ValueError("Tephra2 path is invalid or not executable.")


def export_to_hdf(
    output_df_list, config_file_list, wind_file_list, grid_file, out_file
):
    """Export Tephra2 simulations to binary HDF (.h5) format.

    Parameters
    ----------
    df_list : List of Tephra2 outputs as Pandas DataFrames.
    param_tuple : List of tuples of parameters of tephra2 sims.

    Returns
    -------
    None

    """

    logging.info(f"Exporting data to {out_file}.h5 ...")
    f = h5py.File(f"{out_file}.h5", "w")

    wind_group = f.create_group("wind")

    # Extract non-unique dates from wind filenames
    date_list = [
        re.search(r"(\d{4}-\d{2}-\d{2})", wind_file).group()
        for wind_file in wind_file_list
    ]
    # Drop duplicate wind files
    wind_file_list = list(set(wind_file_list))
    wind_col_names = ["Elevation", "Speed", "Direction"]
    logging.info(f"Exporting wind data between {date_list[0]} and {date_list[-1]}")
    for wind_file in wind_file_list:
        # Extract unique date for wind entry
        wind_date = re.search(r"(\d{4}-\d{2}-\d{2})", wind_file).group()
        # Read wind csv into dataframe
        wind_df = pd.read_csv(wind_file, sep=" ", names=wind_col_names, header=None)
        logging.debug(f"Writing wind data for {wind_date}")
        # Convert dataframe to numpy records array
        wind_rec_arr = wind_df.to_records(index=False)
        # Insert wind into HDF table
        wind_group.create_dataset(f"wind_{wind_date}", data=wind_rec_arr)
        # Delete wind temp file
        os.remove(wind_file)

    # Just adding the grid file to root because we only use one.
    logging.info("Exporting simulation grid coordinates")
    grid_col_names = ["Northing", "Easting", "Elevation"]
    grid_df = pd.read_csv(
        grid_file,
        sep=" ",
        names=grid_col_names,
        header=None,
        comment="#",
        dtype=np.float64,
    )
    grid_rec_arr = grid_df.to_records(index=False)
    f.create_dataset("grid_file", data=grid_rec_arr)

    logging.info("Exporting simulation input and output data")
    sim_group = f.create_group("sims")
    config_group = f.create_group("configs")
    i = 0
    for date, config_file, output_df in zip(
        date_list, config_file_list, output_df_list
    ):
        i += 1
        logging.debug(f"Writing config data for Sim {i} on {date}")
        config_df = pd.read_csv(config_file, sep="\t", index_col=0, names=[None, 0]).T
        config_rec_arr = config_df.to_records(index=False)
        config_group.create_dataset(f"config_{i}", data=config_rec_arr)

        logging.debug(f"Writing output data for Sim {i} on {date}")
        for col in output_df:
            output_df[col] = pd.to_numeric(output_df[col], errors="raise")
        output_rec_arr = output_df.to_records(index=False)
        sim_group.create_dataset(f"sim_{i}", data=output_rec_arr)

    logging.info("Export success. Exiting.")


def extract_tephra2_wind(multiphase_config_file, netcdf_file):
    """
    Extract Tephra2 wind data for each date in the multiphase configuration file.
    """
    wind_dir = "wind_files"
    os.makedirs(wind_dir, exist_ok=True)
    wind_files = []

    # Create NetCDFWindExtractor object
    netcdf_wind_extractor = NetCDFWindExtractor(netcdf_file)

    # Loop through multiphase configuration file
    with open(multiphase_config_file, "r") as config_file:
        next(config_file)  # Skip header
        for line in config_file:
            # Extract date
            date = datetime.strptime(line.split(",")[0], "%Y-%m-%d %H:%M:%S")

            # Extract wind data
            wind_data = netcdf_wind_extractor.extract_tephra2_wind(date)

            # Save wind data to temporary file
            wind_file = os.path.join(wind_dir, f"{date.strftime('%s')}.csv")
            wind_data.to_csv(wind_file, index=False)
            wind_files.append(wind_file)

    return wind_files


def create_tephra2_config_file(params, param_names, filename):
    with open(filename, "w") as f:
        for n, p in zip(param_names, params):
            # For some reason these come in here with weird whitespaces
            n = re.sub("\s+", "", n)
            p = re.sub("\s+", "", p)
            f.write(f"{n.strip()}\t{p.strip()}\n")


def run_tephra2(
    tephra2_path, config_file_path, grid_file_path, wind_file_path, output_file_path
):
    """
    Executes tephra2 with the given configuration, grid, and wind files, and saves the
    output to a file.

    Parameters:
    tephra2_path (str): The path to the tephra2 executable.
    config_file_path (str): The path to the tephra2 configuration file.
    grid_file_path (str): The path to the grid file.
    wind_file_path (str): The path to the wind file.
    output_file_path (str): The path to the file where the tephra2 output should be
    saved.

    Returns:
    None
    """
    # Construct the command to execute tephra2
    command = [tephra2_path, config_file_path, grid_file_path, wind_file_path]

    # Run tephra2 and capture the output
    try:
        logging.debug(
            "Executing Tephra2 command:"
            f" \n{tephra2_path} {config_file_path} {grid_file_path} "
            f"{wind_file_path} > {output_file_path}"
        )
        result = subprocess.run(command, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.critical(f'Tephra2 failed with error code {e.returncode}:"{e.output}"')
        sys.exit(1)
    return result


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Run Tephra2 using a multiphase configuration file."
    )
    parser.add_argument(
        "multiphase_config_file",
        help=(
            "Filename of multiphase configuration file. This file can be generated"
            " using the script tephra2_multiphase_generator.py"
        ),
    )
    parser.add_argument("netcdf_file", help="NetCDF file containing wind data")
    parser.add_argument(
        "grid_file",
        help=(
            "Grid file. This file can be generated using the script"
            " generate_utm_grid.py"
        ),
    )
    parser.add_argument("tephra2_path", help="Path to Tephra2 executable")
    parser.add_argument(
        "out_file",
        help=(
            "Output filename. File will be saved to the HDF format with the filename"
            " <output_filename>.h5"
        ),
    )

    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress all output"
    )
    log_group.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    log_group.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug output"
    )
    args = parser.parse_args()

    # Set up logging
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    elif args.quiet:
        log_level = logging.CRITICAL
    log_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=log_level, format=log_format)

    # Validate input files
    validate_input_files(
        args.multiphase_config_file,
        args.netcdf_file,
        args.grid_file,
        args.tephra2_path,
    )

    total_start_time = time.time()

    # Create NetCDFWindExtractor object
    logging.info("Initialising wind extractor (This takes a while...)")
    start_time = time.time()
    wind_extractor = NetCDFWindExtractor(args.netcdf_file)
    elapsed_time = time.time() - start_time
    logging.info(f"Wind Extractor initialised in {elapsed_time:.2f} seconds")

    # Read in multiphase configuration file
    with open(args.multiphase_config_file) as f:
        multiphase_config = f.readlines()

    _, _, _, *param_names = multiphase_config[0].split(",")

    input_list = []
    wind_file_list = []
    config_file_list = []
    dates_list = []
    phase_type_list = []

    temp_dir = ".temp"
    try:
        os.mkdir(temp_dir)
    except FileExistsError:
        shutil.rmtree(temp_dir)
        os.mkdir(temp_dir)

    # Loop over lines in multiphase configuration file
    for i, line in enumerate(multiphase_config[1:]):
        # Parse line
        date, phase, phase_type, *tephra2_params = line.split(",")

        dates_list += [date]
        phase_type_list += [phase_type]

        # Check if wind file already exists.
        wind_filename = os.path.join(temp_dir, f"wind_{date}.dat")
        if not os.path.exists(wind_filename):
            # Extract wind data
            logging.info(f"Extracting wind data for date {date}")
            start_time = time.time()
            wind_df = wind_extractor.extract_tephra2_wind(date)[0]
            elapsed_time = time.time() - start_time
            logging.debug(f"Wind data extracted in {elapsed_time:.2f} seconds")

            # Write wind data to wind file
            logging.debug(f"Writing wind data to file {wind_filename}")
            start_time = time.time()
            wind_df.to_csv(wind_filename, sep=" ", header=False, index=False)
            elapsed_time = time.time() - start_time
            logging.debug(f"Wind data written to file in {elapsed_time:.2f} seconds")
        wind_file_list += [wind_filename]

        # Create Tephra2 configuration file
        tephra2_filename = os.path.join(
            temp_dir, f"config_file{i:06d}_phase{int(phase):03d}_{date}.dat"
        )
        logging.debug(f"Creating Tephra2 configuration file {tephra2_filename}")
        start_time = time.time()
        create_tephra2_config_file(tephra2_params, param_names, tephra2_filename)
        elapsed_time = time.time() - start_time
        logging.debug(
            f"Tephra2 configuration written to file in {elapsed_time:.2f} seconds"
        )

        output_filename = os.path.join(
            temp_dir, f"output{i:06d}_phase{int(phase):03d}_{date}.dat"
        )

        config_file_list += [tephra2_filename]

        # I have to do it like this to work with starmap, but to save space I'm using
        # links in the output HDF file. I am using more memory this way though.
        param_tuple = (
            args.tephra2_path,
            tephra2_filename,
            args.grid_file,
            wind_filename,
            output_filename,
        )
        input_list += [param_tuple]

    total_elapsed_time = time.time() - total_start_time
    num_processes = mp.cpu_count()
    logging.info("DONE")
    logging.info(
        f"{i} Tephra2 configurations prepared in a total of"
        f" {total_elapsed_time:.2f} seconds."
        f" Commencing Tephra2 executions on {num_processes} cores..."
    )

    pool = mp.Pool(processes=num_processes)

    start_time = time.time()
    results = pool.starmap(run_tephra2, input_list)
    elapsed_time = time.time() - start_time
    logging.info(f"Success. Tephra2 runs executed in {elapsed_time:.2f} seconds")

    res_df_list = []
    for result in results:
        output = result.stdout.decode().splitlines()

        output = [line.replace("#", "").split(" ") for line in output]
        res_df = pd.DataFrame(
            output[1:],
            columns=output[0],
        )
        res_df.replace('', np.nan)
        res_df_list += [res_df]

    export_to_hdf(
        res_df_list,
        config_file_list,
        wind_file_list,
        args.grid_file,
        args.out_file,
    )

    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
