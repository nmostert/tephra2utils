#!/bin/bash

usage() {
  echo "Usage: $(basename $0) -t <tephra2_path> -p <parameter_file> -g <grid_file> -w <wind_file> -o <output_file_prefix>"
  echo "Run Tephra2 with multiple input configurations specified in a parameter file."
  echo
  echo "Options:"
  echo "  -t, --tephra2-path   Path to the Tephra2 executable"
  echo "  -p, --parameter-file Path to the parameter file"
  echo "  -g, --grid-file      Path to the grid file"
  echo "  -w, --wind-file      Path to the wind file"
  echo "  -o, --output-prefix  Prefix for the output file names"
  echo "  -h, --help           Show this help message and exit"
}

tephra2_path=""
parameter_file=""
grid_file=""
wind_file=""
output_file_prefix=""

while getopts ":t:p:g:w:o:h" opt; do
  case ${opt} in
    t )
      tephra2_path=$OPTARG
      ;;
    p )
      parameter_file=$OPTARG
      ;;
    g )
      grid_file=$OPTARG
      ;;
    w )
      wind_file=$OPTARG
      ;;
    o )
      output_file_prefix=$OPTARG
      ;;
    h )
      usage
      exit 0
      ;;
    \? )
      echo "Invalid option: -$OPTARG" >&2
      usage
      exit 1
      ;;
    : )
      echo "Option -$OPTARG requires an argument." >&2
      usage
      exit 1
      ;;
  esac
done
shift $((OPTIND -1))

if [[ -z $tephra2_path || -z $parameter_file || -z $grid_file || -z $wind_file || -z $output_file_prefix ]]; then
  echo "Error: Missing required arguments." >&2
  usage
  exit 1
fi

# Loop through each line in the input file
run=0
while IFS=, read -r line || [[ -n "$line" ]]; do
    if [[ $line == "run"* ]]; then
        params=($(echo "$line" | awk -F "," '{for(i=2;i<=NF;i++) print $i}'))

        echo ${params[@]}
    else
        echo "RUN: $run"
        # Get the parameters and values from the line
        values=($(echo "$line" | awk -F "," '{for(i=2;i<=NF;i++) print $i}'))
        echo ${values[@]}

        # Create a temporary configuration file
        temp_file=$(mktemp temp_config_file.XXXXXX)

        # Write parameter values to temp configuration file
        for (( i=0; i<${#params[@]}; i++ )); do
            echo ${params[$i]} ${values[$i]} >> $temp_file
        done

        # Call the utility with the temporary configuration file
        output_file="${output_file_prefix}_run${run}.txt"
        $tephra2_path $temp_file $grid_file $wind_file > $output_file 
        ((run++))
        rm $temp_file
    fi
done < "$parameter_file"

