import netcdf_wind_extractor as nd
import common_utils
import pandas as pd
import argparse
import importlib
import sys
import numpy as np
from scipy.stats import norm, fisk
import datetime as dt
import logging


def read_multiphase_config(filename):
    config = pd.read_csv(filename)
    return config


def exp_per_day(loc, scale):
    return 10 ** (norm.rvs(loc=loc, scale=scale))


def intexp_repose(k, nexplosions_per_day, a, b):
    val = np.ceil(fisk.rvs(k, nexplosions_per_day, a) / b)
    return val


def cont_repose(k):
    val = np.ceil(np.exp(k + norm.rvs()))
    return val


def generate_phase_runs(config, phase_config_dir, start_date, wind_file):
    # custom_functions = importlib.import_module("custom_functions")

    # Get total duration
    start_datetime = dt.datetime.strptime(start_date, "%Y-%m-%d")

    total_duration = config["Phase Duration"].sum()
    # Following Quiesence column is parsed as a string because the last value is "END".
    # I'm leaving out the last value and parsing the rest to int.
    total_quiescence = config.iloc[0:-1]["Following Quiescence"].astype(int).sum()

    end_datetime = start_datetime + dt.timedelta(
        days=int(total_duration + total_quiescence)
    )

    logging.info(
        f"\nTotal Duration: {total_duration} days"
        f"\nTotal Quiescence: {total_quiescence} days"
        f"\nTotal Eruptive Time: {total_duration + total_quiescence} days."
        f"\nStart Date: {start_datetime}"
        f"\nEnd Date: {end_datetime}"
        f"\n\nStarting generation for {len(config)} phases..."
    )

    event_list = []

    columns = []
    for i, row in config.iterrows():
        phase_type = row["Phase Type"]

        phase_conf_filename = f"{phase_config_dir}{phase_type}_template.conf"
        try:
            phase_conf = common_utils.read_config_file(phase_conf_filename)
            if len(columns) == 0:
                columns = ["DATE"]
                columns += phase_conf.keys()
        except FileNotFoundError:
            print(
                f"ERROR: Phase configuration template file '{phase_conf_filename}' not"
                " found."
            )
            sys.exit(0)
        dur = row["Phase Duration"]
        qui = row["Following Quiescence"]
        tot_dur = config.iloc[0:i]["Phase Duration"].sum()
        tot_qui = config.iloc[0:i]["Following Quiescence"].astype(int).sum()

        phase_start = start_datetime + dt.timedelta(days=float(tot_dur + tot_qui))
        phase_end = phase_start + dt.timedelta(days=(row["Phase Duration"]))
        phase_start_str = phase_start.strftime("%Y-%m-%d")
        phase_end_str = phase_end.strftime("%Y-%m-%d")
        logging.info(
            "_________________________________________________"
            "\n"
            f"\n\t\tPHASE {i}"
            "\n_________________________________________________"
            f"\nType: {phase_type}"
            f"\nDescription: {row.Description}"
            f"\nStart date: {phase_start_str};\tEnd date: {phase_end_str}"
            f"\nDuration: {dur} days"
            "\n..."
        )
        bangs = 0
        if phase_type == "IntExp":
            nexpday = exp_per_day(-0.4772, 1.92)  # Hardcoded K

            phase_day = phase_start

            while phase_day < phase_end:
                bangs += 1
                repose_hours = intexp_repose(4, nexpday, 1, 24)
                run_df = common_utils.generate_runs(phase_conf)
                run_df.insert(0, "PHASE_TYPE", [phase_type])
                run_df.insert(0, "PHASE", [i])
                run_df.insert(0, "DATE", [phase_day.strftime("%Y-%m-%d")])
                event_list += [run_df]
                days_in_phase = (phase_day - phase_start).days
                logging.debug(
                    "BANG"
                    f"\tphase={run_df.PHASE[0]}"
                    f"\ttype={run_df.PHASE_TYPE[0]}"
                    f"\tday={days_in_phase}/{dur}"
                    f"\tdate={run_df.DATE[0]}"
                    f"\theight={run_df.PLUME_HEIGHT[0]/1000:.2f}km"
                    f"\tmass={run_df.ERUPTION_MASS[0]:.2e}kg"
                )
                phase_day += dt.timedelta(hours=float(repose_hours))

        elif phase_type == "Cont":
            phase_day = phase_start

            while phase_day < phase_end:
                bangs += 1
                repose = cont_repose(2.37)  # Hardcoded k value for Cont. eruptions
                run_df = common_utils.generate_runs(phase_conf)
                run_df.insert(0, "PHASE_TYPE", [phase_type])
                run_df.insert(0, "PHASE", [i])
                run_df.insert(0, "DATE", [phase_day.strftime("%Y-%m-%d")])
                event_list += [run_df]
                days_in_phase = (phase_day - phase_start).days
                logging.debug(
                    "BANG"
                    f"\tphase={run_df.PHASE[0]}"
                    f"\ttype={run_df.PHASE_TYPE[0]}"
                    f"\tday={days_in_phase}/{dur}"
                    f"\tdate={run_df.DATE[0]}"
                    f"\theight={run_df.PLUME_HEIGHT[0]/1000:.2f}km"
                    f"\tmass={run_df.ERUPTION_MASS[0]:.2e}kg"
                )
                phase_day += dt.timedelta(days=float(repose))

        else:
            phase_day = phase_start

            phase_length = phase_end - phase_start

            phase_days = phase_length.days

            base_run = common_utils.generate_runs(phase_conf)
            while phase_day < phase_end:
                bangs += 1
                run_df = base_run.copy()
                run_df.insert(0, "PHASE_TYPE", [phase_type])
                run_df.insert(0, "PHASE", [i])
                run_df.insert(0, "DATE", [phase_day.strftime("%Y-%m-%d")])

                run_df.loc[0, "ERUPTION_MASS"] = run_df.ERUPTION_MASS[0] / phase_days
                event_list += [run_df]
                days_in_phase = (phase_day - phase_start).days
                logging.debug(
                    "BANG"
                    f"\tphase={run_df.PHASE[0]}"
                    f"\ttype={run_df.PHASE_TYPE[0]}"
                    f"\tday={days_in_phase}/{dur}"
                    f"\tdate={run_df.DATE[0]}"
                    f"\theight={run_df.PLUME_HEIGHT[0]/1000:.2f}km"
                    f"\tmass={run_df.ERUPTION_MASS[0]:.2e}kg"
                )
                phase_day += dt.timedelta(days=1)
        logging.info(
            f"\nDONE. Generated {bangs} bangs over {dur} days."
            "\n"
        )
        if qui != "END":
            logging.info(
                f"\n........QUIESCENT for {qui} days........"
            )
    logging.info("Preparing dataframe for export...")
    ret_df = pd.concat(event_list, axis=0)
    logging.info("DONE.")
    return ret_df


def main():
    parser = argparse.ArgumentParser(
        description="Generate Tephra2 input files for multiple eruption phases."
    )

    # Required arguments
    parser.add_argument(
        "config_file",
        help=(
            "path to the multiphase configuration file. The file should have columns"
            " for phase type, duration, following quiescence, and description."
        ),
    )
    parser.add_argument(
        "phase_config_dir",
        help=(
            "path to the directory containing the config templates for the eruption"
            ' types specified in the "Type" column of the config_file. The file should'
            " have columns for phase type, duration, following quiescence, and"
            " description."
        ),
    )
    parser.add_argument(
        "wind_file",
        help=(
            "path to the .net pdf wind file from which to extract wind files for each"
            " eruption."
        ),
    )
    parser.add_argument(
        "start_date",
        help=(
            "starting date in YYYY-MM-DD format. This is the date at which phase 0 in"
            " the eruption begins. The dates for subsequent eruptions are calculated"
            " based on the total durations and quiescences of preceding eruptions."
        ),
    )

    # Optional arguments
    parser.add_argument(
        "-o",
        "--output",
        help=(
            "output directory path. If not specified, the output will be written to the"
            " current working directory."
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

    # Configure logging based on command line arguments
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    elif args.quiet:
        log_level = logging.CRITICAL
    logging.basicConfig(level=log_level, format="%(message)s")

    logging.info("Reading configuration file...")
    config = read_multiphase_config(args.config_file)
    logging.info("DONE.")

    mp_df = generate_phase_runs(
        config, args.phase_config_dir, args.start_date, args.wind_file
    )

    if args.output:
        logging.info(f'Saving to file "{args.output}"...')
        mp_df.to_csv(args.output, index=False)
        logging.info("DONE.")
    else:
        logging.info(
            "No output file/directory specified."
            '\nSaving with default filename "output.csv" to current directory...'
        )
        mp_df.to_csv("output.csv", index=False)
        logging.info("DONE.")

    logging.info("Script success. Exiting.")


if __name__ == "__main__":
    main()
