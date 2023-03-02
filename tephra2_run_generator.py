import numpy as np
import random
import sys
import pandas as pd
import re
import argparse
from scipy.stats import lognorm
import importlib


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
                fixed_value_regex = r"-?\d+(?:\.\d+)?(?:e[+-]?\d+)?$"

                # Matches a word (one or more letters, digits or underscores)
                # enclosed in curly braces.
                function_name_regex = r"\{(\w+)\}"

                # Matches a comma-separated list of numbers (with optional
                # decimal point and/or exponent notation) enclosed in square
                # brackets.

                function_value_regex = r'\[((?:-?\d*(?:\.\d+)?' + \
                    r'(?:e[+-]?\d+)?' + \
                    r'|\|[A-Z_]+\|)(?:, ?(?:-?\d*(?:\.\d+)?(?:e[+-]?\d+)?' +\
                    r'|\|[A-Z_]+\|))*)\]'

                param_name_matches = re.findall(param_name_regex, line)
                fixed_value_matches = re.findall(fixed_value_regex, line)
                function_name_matches = re.findall(function_name_regex, line)
                function_value_matches = re.findall(function_value_regex, line)

                config[param_name_matches[0]] = {}

                if fixed_value_matches:
                    config[param_name_matches[0]]["values"] = \
                        [float(fixed_value_matches[0])]
                elif function_name_matches:
                    config[param_name_matches[0]]["sampleFunction"] = \
                        function_name_matches[0]
                    config[param_name_matches[0]]["values"] = []
                    for val in function_value_matches[0].split(","):

                        try:
                            config[param_name_matches[0]]["values"] += \
                                [float(val.strip())]
                        except ValueError:
                            config[param_name_matches[0]]["values"] += \
                                [val.strip()]

    return config


def generate_runs(config_dict, runs):
    custom_functions = importlib.import_module('custom_functions')

    run_params = []

    for param in config_dict:
        if 'sampleFunction' in config_dict[param].keys():
            fun_name = config_dict[param]['sampleFunction']
            if fun_name in globals():
                values = []
                for i in range(runs+1):
                    all_floats = all(isinstance(item, float)
                                     for item in config_dict[param]['values'])
                    if all_floats:
                        values += [
                            globals()[fun_name](*config_dict[param]['values'])
                        ]
                    else:
                        values += [config_dict[param]['values']]
            else:
                try:
                    function = getattr(custom_functions, fun_name)
                    values = []
                    for i in range(runs+1):
                        all_floats = all(isinstance(item, float)
                                         for item
                                         in config_dict[param]['values'])
                        if all_floats:
                            values += [
                                function(*config_dict[param]['values'])
                            ]
                        else:
                            values += [config_dict[param]['values']]
                except ImportError:
                    print(f"ERROR: Unknown sample function \"{fun_name}\"" +
                          f" in config for parameter {param}")
                    sys.exit(0)
            run_params += [values]
        else:
            run_params += [config_dict[param]['values']*(runs+1)]
    run_df = pd.DataFrame(run_params, index=config_dict.keys()).T

    for param in run_df.columns:
        print(run_df[param])
        if not all(isinstance(item, float) for item in run_df[param].values):
            func_vals = []
            for val in run_df[param].values[0]:
                print(val)
                if isinstance(val, float):
                    func_vals += [[val]*len(run_df)]
                else:
                    pattern = r'\|([A-Z_]+)\|'
                    dep_param = re.match(pattern, val).group(1)
                    gen_params = run_df[dep_param].to_list()
                    func_vals += [gen_params]
            print(func_vals)
            gen_values = []
            for splat_params in zip(*func_vals):
                fun_name = config_dict[param]['sampleFunction']
                if fun_name in globals():
                    gen_values += [
                        globals()[fun_name](*splat_params)
                    ]
                else:
                    function = getattr(custom_functions, fun_name)
                    gen_values += [function(*splat_params)]
            print(gen_values)
            run_df[param] = gen_values

    return run_df


def unif(a, b):
    uni = random.uniform(a, b)
    return uni


def log_unif(a, b):
    uni = np.exp(random.uniform(np.log(a), np.log(b)))
    return uni


def trunc_lognorm(mean, std, max_val):
    mu = np.log(mean ** 2 / np.sqrt(std ** 2 + mean ** 2))
    sigma = np.sqrt(np.log(std ** 2 / mean ** 2 + 1))
    sample = lognorm.rvs(s=sigma, scale=np.exp(mu), loc=0, size=1)
    if sample > max_val:
        return max_val
    else:
        return sample


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
