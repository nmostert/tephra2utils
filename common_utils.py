import re
import importlib
import sys
import pandas as pd


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

                function_value_regex = (
                    r"\[((?:-?\d*(?:\.\d+)?"
                    + r"(?:e[+-]?\d+)?"
                    + r"|\|[A-Z_]+\|)(?:, ?(?:-?\d*(?:\.\d+)?(?:e[+-]?\d+)?"
                    + r"|\|[A-Z_]+\|))*)\]"
                )

                param_name_matches = re.findall(param_name_regex, line)
                fixed_value_matches = re.findall(fixed_value_regex, line)
                function_name_matches = re.findall(function_name_regex, line)
                function_value_matches = re.findall(function_value_regex, line)

                config[param_name_matches[0]] = {}

                if fixed_value_matches:
                    config[param_name_matches[0]]["values"] = [
                        float(fixed_value_matches[0])
                    ]
                elif function_name_matches:
                    config[param_name_matches[0]]["sampleFunction"] = (
                        function_name_matches[0]
                    )
                    config[param_name_matches[0]]["values"] = []
                    for val in function_value_matches[0].split(","):
                        try:
                            config[param_name_matches[0]]["values"] += [
                                float(val.strip())
                            ]
                        except ValueError:
                            config[param_name_matches[0]]["values"] += [val.strip()]

    return config


def generate_runs(config_dict, runs=1):
    """
    Generates run parameters using custom functions based on the given configuration
    dictionary.

    Parameters
    ----------
    config_dict : dict
        A dictionary containing the configuration details for the run parameters. Each
        key in the dictionary represents a parameter name, and its value is a dictionary
        containing the following keys:
        'values' - a list of values to be used for the parameter
        'sampleFunction' - (optional) the name of the custom function to be used for
                           sampling values for the parameter.
                           If not specified, the 'values' key will be used as is.
    runs : int, optional
        The number of runs to be generated for each parameter. Defaults to 1.

    Returns
    -------
    run_df : pandas.DataFrame
        A dataframe containing the generated run parameters. Each row of the dataframe
        represents a set of parameter values for a single run, and each column
        represents a parameter.

    Raises
    ------
    ImportError
        If an unknown sample function is specified in the configuration for a parameter.

    """
    custom_functions = importlib.import_module("custom_functions")

    run_params = []

    for param in config_dict:
        if "sampleFunction" in config_dict[param].keys():
            fun_name = config_dict[param]["sampleFunction"]
            try:
                function = getattr(custom_functions, fun_name)
                values = []
                for i in range(runs):
                    all_floats = all(
                        isinstance(item, float) for item in config_dict[param]["values"]
                    )
                    if all_floats:
                        values += [function(*config_dict[param]["values"])]
                    else:
                        values += [config_dict[param]["values"]]
            except ImportError:
                print(
                    f'ERROR: Unknown sample function "{fun_name}"'
                    + f" in config for parameter {param}"
                )
                sys.exit(0)
            run_params += [values]
        else:
            run_params += [config_dict[param]["values"] * (runs)]
    run_df = pd.DataFrame(run_params, index=config_dict.keys()).T

    for param in run_df.columns:
        if not all(isinstance(item, float) for item in run_df[param].values):
            func_vals = []
            for val in run_df[param].values[0]:
                if isinstance(val, float):
                    func_vals += [[val] * len(run_df)]
                else:
                    pattern = r"\|([A-Z_]+)\|"
                    dep_param = re.match(pattern, val).group(1)
                    gen_params = run_df[dep_param].to_list()
                    func_vals += [gen_params]
            gen_values = []
            for splat_params in zip(*func_vals):
                fun_name = config_dict[param]["sampleFunction"]
                if fun_name in globals():
                    gen_values += [globals()[fun_name](*splat_params)]
                else:
                    function = getattr(custom_functions, fun_name)
                    gen_values += [function(*splat_params)]
            run_df[param] = gen_values

    return run_df
