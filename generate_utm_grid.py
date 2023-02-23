import argparse


def generate_utm_grid(
    min_easting,
    max_easting,
    min_northing,
    max_northing,
    spacing
):
    """
    Generate a regular grid of UTM coordinates given four corners of a
    rectangle on a UTM grid and a regular spacing distance.
    :param min_easting: The minimum easting value of the rectangle.
    :param max_easting: The maximum easting value of the rectangle.
    :param min_northing: The minimum northing value of the rectangle.
    :param max_northing: The maximum northing value of the rectangle.
    :param spacing: The regular spacing distance between points in the grid.
    :return: A list of UTM coordinate tuples.
    """
    grid = []
    for northing in range(int(min_northing), int(max_northing), int(spacing)):
        for easting in range(int(min_easting), int(max_easting), int(spacing)):
            grid.append((northing, easting, 1))
    return grid


def main():
    parser = argparse.ArgumentParser(
            description='Generate a regular grid of UTM coordinates.'
            + '\nWARNING: This utility does not work if points are in'
            + 'different UTM zones')
    parser.add_argument(
            'min_easting',
            type=float,
            help='The minimum easting value of the rectangle.')
    parser.add_argument(
            'max_easting',
            type=float,
            help='The maximum easting value of the rectangle.')
    parser.add_argument(
            'min_northing',
            type=float,
            help='The minimum northing value of the rectangle.')
    parser.add_argument(
            'max_northing',
            type=float,
            help='The maximum northing value of the rectangle.')
    parser.add_argument(
            'spacing',
            type=float,
            help='The regular spacing distance between points in the grid.')
    parser.add_argument(
            'output_file',
            type=str,
            nargs='?',
            default='output.txt',
            help='The name of the output file.')

    args = parser.parse_args()

    grid = generate_utm_grid(
            args.min_easting,
            args.max_easting,
            args.min_northing,
            args.max_northing,
            args.spacing)

    with open(args.output_file, 'w') as f:
        f.write('# Northing Easting Elevation\n')
        for coord in grid:
            f.write('{} {} {}\n'.format(coord[0], coord[1], coord[2]))


if __name__ == '__main__':
    main()
