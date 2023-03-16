import argparse
import common_utils


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

    config = common_utils.read_config_file(args.input_file)

    run_df = common_utils.generate_runs(config, args.runs)

    with open(args.output_file, 'w') as f:
        run_df.to_csv(f, index_label="run")


if __name__ == '__main__':
    main()
