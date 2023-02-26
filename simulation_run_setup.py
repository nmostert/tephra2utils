import json
import random
import sys
import pandas as pd


def read_config_params(filename):
    with open(filename) as json_file:
        config = json.load(json_file)
    return config


def generate_runs(config, runs):
    print(runs)
    run_params = []

    for param in config:
        if 'sampleFunction' in config[param].keys():
            fun_name = config[param]['sampleFunction']
            if fun_name in globals():
                values = []
                values += [globals()[fun_name](*config[param]['values'])]
            else:
                print(f"ERROR: Unknown sample function \"{fun_name}\" in " +
                      f"config for parameter {param}")
                sys.exit(0)
            run_params += values
        else:
            run_params += config[param]['values']
    param_dict = {i: [j] for i, j in zip(config.keys(), run_params)}
    run_df = pd.DataFrame(param_dict)

    print(run_df)


def unif(a, b):
    uni = random.uniform(a, b)
    return uni


def main():
    runs = 20
    config = read_config_params("param_config.json")
    generate_runs(config, runs)


if __name__ == '__main__':
    main()
