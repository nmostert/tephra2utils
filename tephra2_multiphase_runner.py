import os
import argparse
import subprocess
from datetime import datetime
from netcdf_wind_extractor import NetCDFWindExtractor
import logging
import time
import sys


def validate_input_files(
    multiphase_config_file, netcdf_file, grid_file, tephra2_path, output_dir
):
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
    for dir_path in [
        tephra2_path,
        output_dir,
    ]:
        if not os.path.exists(dir_path):
            raise ValueError(f"Path/directory {dir_path} not found.")

    # Check if files are valid
    if not multiphase_config_file.endswith(".csv"):
        raise ValueError("Multiphase config file must be a CSV file.")
    if not netcdf_file.endswith(".nc"):
        raise ValueError("NetCDF file must be a NetCDF file.")
    if not grid_file.endswith(".csv"):
        raise ValueError("Grid file must be a CSV file.")
    if not os.access(tephra2_path, os.X_OK):
        raise ValueError("Tephra2 path is invalid or not executable.")


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
            f.write(f"{n}\t{p}\n")


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
    with open(output_file_path, "w") as output_file:
        try:
            subprocess.run(command, stdout=output_file, check=True)
        except subprocess.CalledProcessError as e:
            logging.critical(
                f'Tephra2 failed with error code {e.returncode}:"{e.output}"'
                "\nHere is the failed command in case you want to try it yourself:"
                f"\n{tephra2_path} {config_file_path} {grid_file_path} "
                f"{wind_file_path} > {output_file_path}"
            )
            sys.exit(1)


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
    parser.add_argument("output_dir", help="Output directory")
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
        args.output_dir,
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

    # Loop over lines in multiphase configuration file
    for i, line in enumerate(multiphase_config[1:]):
        # Parse line
        date, phase, phase_type, *tephra2_params = line.split(",")

        # Check if wind file already exists.
        wind_filename = os.path.join(args.output_dir, f"wind_{date}.dat")
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

        # Create Tephra2 configuration file
        tephra2_filename = os.path.join(
            args.output_dir, f"config_file{i:06d}_phase{int(phase):03d}_{date}.dat"
        )
        logging.debug(f"Creating Tephra2 configuration file {tephra2_filename}")
        start_time = time.time()
        create_tephra2_config_file(tephra2_params, param_names, tephra2_filename)
        elapsed_time = time.time() - start_time
        logging.debug(
            f"Tephra2 configuration written to file in {elapsed_time:.2f} seconds"
        )

        # Run Tephra2
        output_filename = os.path.join(
            args.output_dir, f"output{i:06d}_phase{int(phase):03d}_{date}.dat"
        )
        start_time = time.time()
        run_tephra2(
            args.tephra2_path,
            tephra2_filename,
            args.grid_file,
            wind_filename,
            output_filename,
        )
        elapsed_time = time.time() - start_time
        logging.debug(f"Tephra2 run executed in {elapsed_time:.2f} seconds")
        logging.info(f"Tephra2 output saved to {output_filename}")
        total_elapsed_time = time.time() - total_start_time
        logging.debug(f"Total elapsed time: {total_elapsed_time:.2f}")

    total_elapsed_time = time.time() - total_start_time
    logging.info(
        f"DONE.{i} Tephra2 runs executed in a total of"
        f" {total_elapsed_time:.2f} seconds."
    )


if __name__ == "__main__":
    main()
