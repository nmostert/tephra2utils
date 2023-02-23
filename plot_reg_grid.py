import argparse
import numpy as np
import pandas as pd
import folium
import utm
import re


def plot_regular_grid(input_file, utm_zone, output_file):
    # Read in the CSV file
    df = pd.read_csv(
            input_file,
            comment='#',
            sep=' ',
            names=["Northing", "Easting", "Elevation"])

    # Extract the Northing and Easting columns
    northing = df['Northing'].tolist()
    easting = df['Easting'].tolist()

    # Extract UTM zone info
    zone_number, zone_letter = re.match(r'(\d+)?([A-Z])', utm_zone).groups()

    # Find map center
    n0 = np.mean(northing)
    e0 = np.mean(easting)
    lat0, lon0 = utm.to_latlon(
        e0,
        n0,
        int(zone_number),
        zone_letter)

    # Create a map centered at (lat0, lon0)
    m = folium.Map(
        location=[lat0, lon0],
        zoom_start=10,
        tiles="Stamen Terrain"
    )

    # Add a marker for each coordinate
    for i in range(len(northing)):
        latitude, longitude = utm.to_latlon(
            easting[i],
            northing[i],
            int(zone_number),
            zone_letter)
        folium.CircleMarker(
            location=[latitude, longitude],
            radius=1,
            color="red",
            fill=False,
        ).add_to(m)

    # Save the map as an HTML file
    m.save(output_file)


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(
            description='Plot UTM coordinates on a world map.')
    parser.add_argument('input_file', type=str, help='the input CSV file')
    parser.add_argument('utm_zone', type=str, help='The UTM Zone')
    parser.add_argument('output_file', type=str, help='the output HTML file')
    args = parser.parse_args()

    # Call the plot_coordinates function with the command line arguments
    plot_regular_grid(args.input_file, args.utm_zone, args.output_file)
