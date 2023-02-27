import numpy as np
import random
import sys
import pandas as pd
import re
import argparse


def read_config_file(filename):
    config = {}
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line == "" and not line.startswith("#"):
                # Matches uppercase word at start of line
                param_name_regex = r"^[A-Z_]+"

                # Matches numbers (with optional decimal points and/or
                # exponent notation) at the end of a line.
                fixed_value_regex = r"\d+(?:\.\d+)?(?:e[+-]?\d+)?$"

                # Matches a word (one or more letters, digits or underscores)
                # enclosed in curly braces.
                function_name_regex = r"\{(\w+)\}"

                # Matches a comma-separated list of numbers (with optional
                # decimal point and/or exponent notation) enclosed in square
                # brackets.
                function_value_regex = r"\[(\d+(?:\.\d+)?(?:e[+-]?\d+)?" \
                    + r"(?:,\s*\d+(?:\.\d+)?(?:e[+-]?\d+)?)*?)\]"

                param_name_matches = re.findall(param_name_regex, line)
                fixed_value_matches = re.findall(fixed_value_regex, line)
                function_name_matches = re.findall(function_name_regex, line)
                function_value_matches = re.findall(function_value_regex, line)
                print(function_value_matches)

                config[param_name_matches[0]] = {}

                if fixed_value_matches:
                    config[param_name_matches[0]]["values"] = \
                        [float(fixed_value_matches[0])]
                elif function_name_matches:
                    config[param_name_matches[0]]["sampleFunction"] = \
                        function_name_matches[0]
                    config[param_name_matches[0]]["values"] = \
                        [float(val.strip()) for val in
                            function_value_matches[0].split(",")]

    return config


def generate_runs(config_dict, runs):
    run_params = []

    for param in config_dict:
        if 'sampleFunction' in config_dict[param].keys():
            fun_name = config_dict[param]['sampleFunction']
            if fun_name in globals():
                values = []
                for i in range(runs+1):
                    values += [
                            globals()[fun_name](*config_dict[param]['values'])
                        ]
            else:
                print(f"ERROR: Unknown sample function \"{fun_name}\" in " +
                      f"config for parameter {param}")
                sys.exit(0)
            run_params += [values]
        else:
            run_params += [config_dict[param]['values']*(runs+1)]
    run_df = pd.DataFrame(run_params, index=config_dict.keys()).T

    return run_df


def unif(a, b):
    uni = random.uniform(a, b)
    return uni


def log_unif(a, b):
    uni = np.exp(random.uniform(np.log(a), np.log(b)))
    return uni


def main():
    parser = argparse.ArgumentParser(
            description='Generate configurations for a Tephra2 simulation run.'
        )
    parser.add_argument(
            'input_file',
            type=str,
            help='Name of input file. Input file should contain lines of the' +
            'format \n<PARAMETER_NAME> <fixed_value>\n or ' +
            '\n <PARAMETER_NAME> {<sample_function_name>} ' +
            '[<param_1>, <param_2>, ...]\n' +
            'where sample_function_name(param_1, param_2, ...) is a function' +
            ' defined in the python script that generates a single value for' + 
            ' PARAMETER_NAME.'
            )
    parser.add_argument('runs', type=int, help='Number of runs to generate')
    parser.add_argument('output_file', type=str, help='Name of output file')
    args = parser.parse_args()

    config = read_config_file(args.input_file)

    run_df = generate_runs(config, args.runs)

    with open(args.output_file, 'w') as f:
        run_df.to_csv(f, index_label="run")


if __name__ == '__main__':
    main()
