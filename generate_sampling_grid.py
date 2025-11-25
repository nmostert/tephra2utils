import argparse


def generate_sample_grid(
    ventEast,
    ventNorth,
    min_easting,
    max_easting,
    min_northing,
    max_northing,
    spacing
):
    """
    Generate a regular grid of coordinates given four corners of a
    rectangle on a metre grid and a regular spacing distance.
    This will generate on that spacing grid, without the central point.
    :param min_easting: The minimum easting value of the rectangle.
    :param max_easting: The maximum easting value of the rectangle.
    :param min_northing: The minimum northing value of the rectangle.
    :param max_northing: The maximum northing value of the rectangle.
    :param spacing: The regular spacing distance between points in the grid.
    :return: A list of coordinate tuples.
    """
    grid = []
    for northing in range(int(min_northing), int(max_northing+1), int(spacing)):
        for easting in range(int(min_easting), int(max_easting+1), int(spacing)):
            if not (northing == ventNorth and easting == ventEast):
                grid.append((northing, easting, 1))
    #Now add in the other points at 1 km
    grid.append((ventNorth+1000,ventEast,1))
    grid.append((ventNorth-1000,ventEast,1))
    grid.append((ventNorth,ventEast+1000,1))
    grid.append((ventNorth,ventEast-1000,1))
    #Now the 5 km
    grid.append((ventNorth+5000,ventEast,1))
    grid.append((ventNorth-5000,ventEast,1))
    grid.append((ventNorth,ventEast+5000,1))
    grid.append((ventNorth,ventEast-5000,1))
    #Now the 2 km offset
    grid.append((ventNorth+2000,ventEast+2000,1))
    grid.append((ventNorth-2000,ventEast-2000,1))
    grid.append((ventNorth+2000,ventEast-2000,1))
    grid.append((ventNorth-2000,ventEast+2000,1))
    #Now at 4 km
    grid.append((ventNorth+5000,ventEast+5000,1))
    grid.append((ventNorth-5000,ventEast-5000,1))
    grid.append((ventNorth+5000,ventEast-5000,1))
    grid.append((ventNorth-5000,ventEast+5000,1))
    return grid


def main():
    parser = argparse.ArgumentParser(
            description='Generate a sampling grid of coordinates.'
            + '\nThis utility spits out a regular grid and inner'
            + 'sampling grid at +,- 5km, 1 km and 2km in NE,NW,SW,SE quadrants')
    parser.add_argument(
            'vent_east',
            type=float,
            help='The easting of the vent')
    parser.add_argument(
            'vent_north',
            type=float,
            help='The northing of the vent')
    parser.add_argument(
            'dist_east',
            type=float,
            help='The distance east of the vent.')
    parser.add_argument(
            'dist_west',
            type=float,
            help='The distance west the vent.')
    parser.add_argument(
            'dist_north',
            type=float,
            help='The distance north the vent.')
    parser.add_argument(
            'dist_south',
            type=float,
            help='The distance south of the vent.')
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
    min_easting = args.vent_east - args.dist_west
    max_easting = args.vent_east + args.dist_east
    min_northing = args.vent_north - args.dist_south
    max_northing = args.vent_north + args.dist_north
    grid = generate_sample_grid(
            args.vent_east,
            args.vent_north,
            min_easting,
            max_easting,
            min_northing,
            max_northing,
            args.spacing)

    with open(args.output_file, 'w') as f:
        f.write('# Northing Easting Elevation\n')
        for coord in grid:
            f.write('{} {} {}\n'.format(coord[0], coord[1], coord[2]))


if __name__ == '__main__':
    main()
