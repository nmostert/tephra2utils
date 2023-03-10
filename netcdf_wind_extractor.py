import xarray as xr
import argparse
import pandas as pd
import numpy as np
import datetime as dt
from typing import List
from functools import reduce


class NetCDFWindExtractor:

    def __init__(self, netcdf_file_path):
        """
        Initialize the NetCDFWindExtractor instance.

        Parameters:
        -----------
        netcdf_file_path : str
            The path to the NetCDF file containing wind data.
        """
        self.netcdf_file_path = netcdf_file_path
        self.df = read_ncdf(netcdf_file_path)

    def _read_ncdf(self):
        """
        Read the NetCDF file containing wind data into a pandas dataframe.

        Returns:
        --------
        pandas.DataFrame
            The wind data as a pandas dataframe.
        """
        return read_ncdf(self.netcdf_file_path)

    def extract_tephra2_wind(self, dates):
        """
        Extract wind data for a list of dates.

        Parameters:
        -----------
        dates : list of str
            The dates for which wind data is to be extracted.

        Returns:
        --------
        pandas.DataFrame
            The wind data for the given dates as a pandas dataframe.
        """
        dates_expanded = [parse_date_arg(date) for date in dates]
        dates_list = sum(dates_expanded, [])
        winds = extract_tephra2_wind(self.df, dates_list)
        return winds


def read_ncdf(ncdf_file):
    """
    Read wind data from a NetCDF file and return it as a pandas dataframe.

    Parameters:
    -----------
    ncdf_file : str
        The path to the NetCDF file containing wind data.

    Returns:
    --------
    pandas.DataFrame
        The wind data as a pandas dataframe.
    """
    ds = xr.open_dataset(ncdf_file)
    df = ds.to_dataframe()

    print(df)
    df = df["speed"].unstack(level=1)

    # Parsing multiindex values to be dates and ints respectively
    new_tuples = df.index.map(lambda x: (
        pd.to_datetime(x[0].total_seconds(), unit="s", origin="unix"),
        int(x[1])
    ))
    df.index = pd.MultiIndex.from_tuples(new_tuples,
                                         names=["Time", "wind direction"])

    # Aggregate to daily level (stacking and unstacking because multiindex)
    df = df.unstack(level=1)\
        .resample('D').mean()\
        .stack(level=1)

    return df


def get_wind_speed_and_angle(u, v):
    """
    Calculates wind speed and angle from U and V wind components.

    Parameters
    ----------
    u : pandas.Series or numpy.ndarray
        U-component of wind data.
    v : pandas.Series or numpy.ndarray
        V-component of wind data.

    Returns
    -------
    tuple
        A tuple containing the wind speed and angle in degrees.
        The wind speed and angle are both numpy arrays with the
        same shape as u and v.
    """
    speed = np.sqrt(u**2 + v**2)  # calculate wind speed
    angle = np.arctan2(v, u) * 180 / np.pi  # calculate wind angle in radians

    # convert to degrees and adjust for clockwise from Northing
    angle = (90 - angle) % 360

    return speed, angle


def extract_tephra2_wind(
    ncdf_df: pd.DataFrame, dates: List[dt.datetime]
) -> List[pd.DataFrame]:
    """
    Extracts wind data from a NetCDF DataFrame for a list of given dates.

    Parameters:
    ----------
    ncdf_df : pd.DataFrame
        A pandas DataFrame containing the NetCDF data, with a MultiIndex of
        (date, wind direction).
    dates : List[datetime]
        A list of datetime objects representing the dates to extract wind data
        for.

    Returns:
    -------
    List[pd.DataFrame]
        A list of pandas DataFrames containing the wind data for each date in
        dates.
    """

    # Convert datetime objects to date strings in the format required by the
    # NetCDF DataFrame.
    date_strings = [date.strftime('%Y-%m-%d') for date in dates]

    # Extract wind data for each date in dates.
    wind_df_list = []
    for d in date_strings:
        # Select wind data for the given date and wind directions.
        wind_u = ncdf_df.loc[(d, 1), :]
        wind_v = ncdf_df.loc[(d, 2), :]

        # Compute wind speed and angle from the wind components.
        speed, angle = get_wind_speed_and_angle(wind_u, wind_v)

        # Create a DataFrame with the wind speed and angle data, indexed by
        # hour.
        wind_df = pd.DataFrame(
                {'Speed': speed, 'Angle': angle}, index=range(1, 38))
        wind_df_list += [wind_df]

    return wind_df_list


def parse_date_arg(date_arg: str) -> List[dt.date]:
    """
    Parses a date argument in one of the following formats:
        - 'YYYY-MM-DD': single date
        - 'YYYY-MM-DD:YYYY-MM-DD': date range
        - file path with one date per line

    Parameters
    ----------
    date_arg : str
        The date argument to parse

    Returns
    -------
    List[datetime.date]
        List of datetime.date objects representing the dates in the argument

    Raises
    ------
    argparse.ArgumentTypeError
        If the date argument is not in a valid format
    """
    dates = []
    # Check if date_arg is a single date
    try:
        date = dt.datetime.strptime(date_arg, '%Y-%m-%d').date()
        dates.append(date)
        return dates
    except ValueError:
        pass
    # Check if date_arg is a date range
    try:
        start_date_str, end_date_str = date_arg.split(':')
        start_date = dt.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = dt.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        while start_date <= end_date:
            dates.append(start_date)
            start_date += dt.timedelta(days=1)
        return dates
    except ValueError:
        pass
    # Check if date_arg is a file with a list of dates
    try:
        with open(date_arg, 'r') as f:
            for line in f:
                date_str = line.strip()
                date = dt.datetime.strptime(date_str, '%Y-%m-%d').date()
                dates.append(date)
        return dates
    except (IOError, ValueError):
        pass
    # If the date_arg is not in a valid format, raise an error
    raise argparse.ArgumentTypeError(f'Invalid date argument: {date_arg}')


def save_to_file(wind_df_list, date_list, output_file, aggregate=False):
    """
    Save wind data to file in CSV format.

    Parameters
    ----------
    wind_df_list : List[pandas.DataFrame]
        List of pandas DataFrames containing wind data.
    date_list : List[datetime.date]
        List of datetime.date objects corresponding to the dates for which
        wind data was extracted.
    output_file : str
        Path and base name for the output CSV files. Date strings will be
        appended to this base name.
    aggregate : bool (default: False)
        If True, all dataframes in the least are aggregated to produce a single
        mean wind field.
    Returns
    -------
    None

    """

    # Convert date objects to date strings
    date_strings = [date.strftime('%Y-%m-%d') for date in date_list]

    if aggregate:
        # Calculat the mean wind field and save it to a single file.
        df_mean = reduce(lambda x, y: x.add(y, fill_value=0), wind_df_list) /\
                len(wind_df_list)
        filename = f"{output_file}_mean.csv"
        df_mean.to_csv(filename, sep=' ', header=False)
    else:
        # Loop through each date and DataFrame and save to a separate file
        for date, df in zip(date_strings, wind_df_list):
            filename = f"{output_file}_{date}.csv"
            df.to_csv(filename, sep=' ', header=False)


def main():
    parser = argparse.ArgumentParser(
            description='Utility for converting wind data in a netcdf file' +
                        'to Tephra2 format')
    parser.add_argument(
            'netcdf_file', metavar='netcdf_file', type=str,
            help='Path to the netcdf file containing wind data')
    parser.add_argument(
            'output_file', metavar='output_file', type=str,
            help='Path/prefix for the output file/files')
    parser.add_argument(
            'date', metavar='date', type=str, nargs='+',
            help='Date(s) to extract in yyyy-mm-dd format.' +
            'Can be a single date, a date range (in the form of start_date:' +
            'end_date), a list of dates separated by spaces,' +
            'or a file containing a date on each line.')
    parser.add_argument(
            '-a', '--aggregate', action='store_true',
            help='If set, all files in the date range will be aggregated' +
            ' using the mean to a single output file.')

    args = parser.parse_args()
    dates_expanded = [parse_date_arg(date) for date in args.date]
    dates_list = sum(dates_expanded, [])

    nd = NetCDFWindExtractor(args.netcdf_file)

    # for date in dates_list:
    #     print(date.strftime('%Y-%m-%d'))

    wind_df_list = extract_tephra2_wind(nd.df, dates_list)

    save_to_file(
            wind_df_list,
            dates_list,
            args.output_file,
            aggregate=args.aggregate)


if __name__ == '__main__':
    main()
