"""
The ``wind_turbine`` module contains the class WindTurbine that implements
a wind turbine in the windpowerlib and functions needed for the modelling of a
wind turbine.

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import pandas as pd
import logging
import sys
import requests
import os


class WindTurbine(object):
    r"""
    Defines a standard set of wind turbine attributes.

    Parameters
    ----------
    name : string
        Name of the wind turbine type.
        Use :py:func:`~.get_turbine_types` to see a table of all wind turbines
        for which power (coefficient) curve data is provided.
    hub_height : float
        Hub height of the wind turbine in m.
    rotor_diameter : None or float
        Diameter of the rotor in m. Default: None.
    power_coefficient_curve : None, pandas.DataFrame, dictionary or string
        Power coefficient curve of the wind turbine. DataFrame/dictionary must
        have 'wind_speed' and 'value' columns/keys with wind speeds
        in m/s and the corresponding power coefficients. Default: None.
    power_curve : None, pandas.DataFrame or dictionary or string
        Power curve of the wind turbine. DataFrame/dictionary must have
        'wind_speed' and 'value' columns/keys with wind speeds in m/s and the
        corresponding power curve value in W. Alternatively you can load power
        curve data from the OpenEnergy Database ('oedb') or a file
        ('<path including file name>'). Default: 'oedb'.
    nominal_power : None, float or string
        The nominal output of the wind turbine in W. Alternatively you can load
        the nominal power from the OpenEnergy Database ('oedb') or a file
        ('<path including file name>'). Default: 'oedb'.
    coordinates : list or None
        List of coordinates [lat, lon] of location for loading data.
        Default: None.

    Attributes
    ----------
    name : string
        Name of the wind turbine type.
        Use :py:func:`~.get_turbine_types` to see a table of all wind turbines
        for which power (coefficient) curve data is provided.
    hub_height : float
        Hub height of the wind turbine in m.
    rotor_diameter : None or float
        Diameter of the rotor in m. Default: None.
    power_coefficient_curve : None, pandas.DataFrame or dictionary
        Power coefficient curve of the wind turbine. DataFrame/dictionary must
        have 'wind_speed' and 'value' columns/keys with wind speeds
        in m/s and the corresponding power coefficients. Default: None.
    power_curve : None, pandas.DataFrame or dictionary
        Power curve of the wind turbine. DataFrame/dictionary must have
        'wind_speed' and 'value' columns/keys with wind speeds in m/s and the
        corresponding power curve value in W. Default: None.
    nominal_power : None or float
        The nominal output of the wind turbine in W. Default: None.
    coordinates : list or None
        List of coordinates [lat, lon] of location for loading data.
        Default: None.
    power_output : pandas.Series
        The calculated power output of the wind turbine. Default: None.

    Notes
    ------
    Your wind turbine object should have a power coefficient or power curve.
    If you use the default values for the parameters `power_curve`,
    `power_coefficient_curve` and `nominal_power` ('oedb') the respective data
    is automatically fetched from a data set provided in the OpenEnergy
    Database (oedb). If you want to read files provided by yourself you can
    set the parameters to a string pointing to the file location(s).
    See `example_power_curves.csv', `example_power_coefficient_curves.csv`
    and `example_nominal_power.csv` in example/data for the required form of
    such csv files.

    Examples
    --------
    >>> from windpowerlib import wind_turbine
    >>> enerconE126 = {
    ...    'hub_height': 135,
    ...    'rotor_diameter': 127,
    ...    'name': 'E-126/4200'}
    >>> e126 = wind_turbine.WindTurbine(**enerconE126)
    >>> print(e126.nominal_power)
    4200000.0

    """

    def __init__(self, name, hub_height, rotor_diameter=None,
                 power_coefficient_curve='oedb', power_curve='oedb',
                 nominal_power='oedb', coordinates=None, **kwargs):

        self.name = name
        self.hub_height = hub_height
        self.rotor_diameter = rotor_diameter
        self.power_coefficient_curve = power_coefficient_curve
        self.power_curve = power_curve
        self.nominal_power = nominal_power
        self.coordinates = coordinates

        self.power_output = None

        self.fetch_turbine_data()

    def fetch_turbine_data(self):
        r"""
        Fetches data of the requested wind turbine.

        Depending on the WindTurbine parameters `power_curve`,
        `power_coefficient_curve` and `nominal_power` the methods fetches
        nominal power and/or power coefficient curve and/or power curve from a
        data set provided in the OpenEnergy Database ('oedb') or from a file
        ('<path including file name>'). In case of not being of type string the
        parameters stay as they are (None, float, pd.DataFrame).

        If you want to import your own power (coefficient) curves and/or
        nominal power from files the wind speeds in m/s have to be in the first
        row and the corresponding power coefficient curve values or power curve
        values in W in a row where the first column contains the turbine name.
        See `example_power_curves.csv', `example_power_coefficient_curves.csv`
        and `example_nominal_power.csv` in example/data for the required form
        of the files.
        See :py:func:`~.get_turbine_data_from_file` for an example reading data
        from a csv file.

        Returns
        -------
        self

        Examples
        --------
        >>> from windpowerlib import wind_turbine
        >>> enerconE126 = {
        ...    'hub_height': 135,
        ...    'rotor_diameter': 127,
        ...    'name': 'E-126/4200'}
        >>> e126 = wind_turbine.WindTurbine(**enerconE126)
        >>> print(e126.power_coefficient_curve['value'][5])
        0.44
        >>> print(e126.nominal_power)
        4200000.0

        """
        def specify_data(data_specification, fetch_curve):
            r"""
            Helper function for :py:func:`~.wind_turbine.WindTurbine.fetch_turbine_data`.

            Parameters
            ----------
            data_specification : None, pandas.DataFrame, float, dict or str
                Specifies whether turbine data is not fetched (None, dict,
                pandas.DataFrame, float), is fetched from the oedb ('oedb') or
                is fetched from a provided file (other string than 'oedb').
            fetch_curve : str
                Specifies the type of data being fetched.

            Returns
            -------
            data : None, pandas.DataFrame, float or dict
                Fetched data or `data_specification` if it was not a string.

            """

            if (data_specification is None or
                    isinstance(data_specification, pd.DataFrame) or
                    isinstance(data_specification, float)):
                data = data_specification
                logging.debug("{} is of type {} and wasn't changed.".format(
                    fetch_curve, type(data_specification))) # todo keep or delete?
            elif data_specification == 'oedb':
                data = get_turbine_data_from_oedb(
                    turbine_type=self.name, fetch_curve=fetch_curve)
            elif isinstance(data_specification, str):
                data = get_turbine_data_from_file(
                    turbine_type=self.name, file_=data_specification)
            else:
                data = data_specification
                logging.debug("{} is of type {} and does not match ".format(
                    fetch_curve, type(data_specification)) + "the options.")
            return data

        self.power_curve = specify_data(
            data_specification=self.power_curve, fetch_curve='power_curve')
        self.power_coefficient_curve = specify_data(
            data_specification=self.power_coefficient_curve,
            fetch_curve='power_coefficient_curve')
        self.nominal_power = specify_data(
            data_specification=self.nominal_power,
            fetch_curve='nominal_power')

        return self


def get_turbine_data_from_file(turbine_type, file_):
    r"""
    Fetches turbine data from a csv file.

    See `example_power_curves.csv', `example_power_coefficient_curves.csv` and
    `example_nominal_power_data.csv` in example/data for the required format of
    a csv file.

    Parameters
    ----------
    turbine_type : str
        Specifies the turbine type data is fetched for.
    file_ : str
        Specifies the source of the turbine data.
        See the example below for how to use the example data.

    Returns
    -------
    data : pandas.DataFrame or float
        Power curve or power coefficient curve (pandas.DataFrame) or nominal
        power (float) of one wind turbine type. Power (coefficient) curve
        DataFrame contains power coefficient curve values (dimensionless) or
        power curve values (in dimension given in file) with the corresponding
        wind speeds (in dimension given in file).

    Examples
    --------
    >>> from windpowerlib import wind_turbine
    >>> import os
    >>> source = os.path.join(os.path.dirname(__file__), '../example/data',
    ...                       'example_power_curves.csv')
    >>> p_nom_source = os.path.join(os.path.dirname(__file__),
    ...                             '../example/data',
    ...                             'example_nominal_power.csv')
    >>> example_turbine = {
    ...    'hub_height': 100,
    ...    'rotor_diameter': 70,
    ...    'name': 'DUMMY 3',
    ...    'power_curve': source,
    ...    'power_coefficient_curve': None,
    ...    'nominal_power': p_nom_source}
    >>> e_t_1 = wind_turbine.WindTurbine(**example_turbine)
    >>> print(e_t_1.power_curve['value'][7])
    18000.0
    >>> print(e_t_1.nominal_power)
    150000.0

    """
    try:
        df = pd.read_csv(file_, index_col=0)
    except FileNotFoundError:
        raise FileNotFoundError("The file '{}' was not found.".format(file_))
    wpp_df = df[df.index == turbine_type]
    # if turbine not in data file
    if wpp_df.shape[0] == 0:
        pd.set_option('display.max_rows', len(df))
        logging.info('Possible types: \n{0}'.format(pd.DataFrame(df.index)))
        pd.reset_option('display.max_rows')
        sys.exit('Cannot find the wind converter type: {0}'.format(
            turbine_type))
    # if turbine in data file select power (coefficient) curve columns and
    # change the format or select nominal power
    if 'nominal_power' in file_:
        data = float(wpp_df['nominal_power'].values[0])
    else:
        curve_data = wpp_df.dropna(axis=1)
        data = curve_data.transpose().reset_index()
        data.columns = ['wind_speed', 'value']
        # transform wind speeds to floats
        data['wind_speed'] = data['wind_speed'].apply(lambda x: float(x))
    return data


def get_turbine_data_from_oedb(turbine_type, fetch_curve):
    r"""
    Fetches wind turbine data from the OpenEnergy database (oedb).

    If turbine data exists in local repository it is loaded from this file. The
    file is created when turbine data is loaded from oedb in
    :py:func:`~.load_turbine_data_from_oedb`.

    Execute :py:func:`~.load_turbine_data_from_oedb` or delete the files to
    refresh the download.

    Parameters
    ----------
    turbine_type : str
        Specifies the turbine type data is fetched for.
        Use :py:func:`~.get_turbine_types` to see a table of all wind turbines
        in oedb containing information about whether power (coefficient) curve
        data is provided.
    fetch_curve : str
        Parameter to specify whether a power or power coefficient curve
        should be retrieved from the provided turbine data. Valid options are
        'power_curve' and 'power_coefficient_curve'. Default: None.

    Returns
    -------
    data : pandas.DataFrame or float
        Power curve or power coefficient curve (pandas.DataFrame) or nominal
        power in W (float) of one wind turbine type. Power (coefficient) curve
        DataFrame contains power coefficient curve values (dimensionless) or
        power curve values in W with the corresponding wind speeds in m/s.

    """
    if fetch_curve == 'nominal_power':
        filename = os.path.join(os.path.dirname(__file__), 'data',
                                'oedb_{}.csv'.format(fetch_curve))
    else:
        filename = os.path.join(os.path.dirname(__file__), 'data',
                                'oedb_{}s.csv'.format(fetch_curve))
    if not os.path.isfile(filename):
        # Load data from oedb and save to csv file
        load_turbine_data_from_oedb()
    else:
        logging.debug("Turbine data is fetched from {}".format(filename))

    data = get_turbine_data_from_file(turbine_type=turbine_type,
                                                   file_=filename)

    # nominal power and power curve values in W
    if fetch_curve == 'nominal_power':
        data = data * 1000
    if fetch_curve == 'power_curve':
        # power in W
        data['value'] = data['value'] * 1000
    return data


def load_turbine_data_from_oedb():
    r"""
    Loads turbine data from the OpenEnergy database (oedb).

    Turbine data is saved to csv files ('oedb_power_curves.csv' and
    'oedb_power_coefficient_curves.csv') for offline usage of windpowerlib.
    If the files already exist they are overwritten.

    Returns
    -------
    turbine_data : pd.DataFrame
        Contains turbine data of different turbines such as 'manufacturer',
        'turbine_type', 'nominal_power'.

    """
    # url of OpenEnergy Platform that contains the oedb
    oep_url = 'http://oep.iks.cs.ovgu.de/'
    # location of data
    schema = 'supply'
    table = 'turbine_library'
    # load data
    result = requests.get(
        oep_url + '/api/v0/schema/{}/tables/{}/rows/?'.format(
            schema, table), )
    if not result.status_code == 200:
        raise ConnectionError("Database connection not successful. "
                              "Response: [{}]".format(result.status_code))
    # extract data to data frame
    turbine_data = pd.DataFrame(result.json())
    # standard file name for saving data
    filename = os.path.join(os.path.dirname(__file__), 'data',
                            'oedb_{}.csv')
    # get all power (coefficient) curves and save to file
    # for curve_type in ['power_curve', 'power_coefficient_curve']:
    for curve_type in ['power_curve', 'power_coefficient_curve']:
        curves_df = pd.DataFrame(columns=['wind_speed'])
        for index in turbine_data.index:
            if (turbine_data['{}_wind_speeds'.format(curve_type)][index]
                    and turbine_data['{}_values'.format(curve_type)][index]):
                df = pd.DataFrame(data=[
                    eval(turbine_data['{}_wind_speeds'.format(curve_type)][
                             index]),
                    eval(turbine_data['{}_values'.format(curve_type)][
                             index])]).transpose().rename(
                    columns={0: 'wind_speed',
                             1: turbine_data['turbine_type'][index]})
                curves_df = pd.merge(left=curves_df, right=df, how='outer',
                                     on='wind_speed')
        curves_df = curves_df.set_index('wind_speed').sort_index().transpose()
        curves_df.to_csv(filename.format('{}s'.format(curve_type)))

    # get nominal power of all wind turbine types and save to file
    nominal_power_df = turbine_data[
        ['turbine_type', 'installed_capacity']].set_index(
        'turbine_type').rename(
        columns={'installed_capacity': 'nominal_power'})
    nominal_power_df.to_csv(filename.format('nominal_power'))
    return turbine_data


def get_turbine_types(print_out=True, filter_=True):
    r"""
    Get all wind turbine types provided in the OpenEnergy database (oedb).

    By default only turbine types for which a power coefficient curve or power
    curve is provided are returned. Set `filter_=False` to see all turbine
    types for which any data (f.e. hub height, rotor diameter, ...) is
    provided.

    Parameters
    ----------
    print_out : bool
        Directly prints a tabular containing the turbine types in column
        'turbine_type', the manufacturer in column 'manufacturer' and
        information about whether a power (coefficient) curve exists (True) or
        not (False) in columns 'has_power_curve' and 'has_cp_curve'.
        Default: True.
    filter_ : bool
        If True only turbine types for which a power coefficient curve or
        power curve is provided in the OpenEnergy database (oedb) are
        returned. Default: True.

    Returns
    -------
    pd.DataFrame
        Contains turbine types in column 'turbine_type', the manufacturer in
        column 'manufacturer' and information about whether a power
        (coefficient) curve exists (True) or not (False) in columns
        'has_power_curve' and 'has_cp_curve'.

    Notes
    -----
    If the power (coefficient) curve of the desired turbine type (or the
    turbine type itself) is missing you can contact us via github or
    windpowerlib@rl-institut.de. You can help us by providing data in the
    format as shown in
    `the data base <https://openenergy-platform.org/dataedit/view/model_draft/openfred_windpower_powercurve>`_.

    Examples
    --------
    >>> from windpowerlib import wind_turbine
    >>> df = wind_turbine.get_turbine_types(print_out=False)
    >>> print(df[df["turbine_type"].str.contains("E-126")].iloc[0])
    manufacturer          Enercon
    turbine_type       E-126/4200
    has_power_curve          True
    has_cp_curve             True
    Name: 5, dtype: object
    >>> print(df[df["manufacturer"].str.contains("Enercon")].iloc[0])
    manufacturer          Enercon
    turbine_type       E-101/3050
    has_power_curve          True
    has_cp_curve             True
    Name: 1, dtype: object

    """

    df = load_turbine_data_from_oedb()
    if filter_:
        cp_curves_df = df.loc[df['has_cp_curve']][
            ['manufacturer', 'turbine_type', 'has_cp_curve']]
        p_curves_df = df.loc[df['has_power_curve']][
            ['manufacturer', 'turbine_type', 'has_power_curve']]
        curves_df = pd.merge(p_curves_df, cp_curves_df, how='outer',
                             sort=True).fillna(False)
    else:
        curves_df = df[['manufacturer', 'turbine_type', 'has_power_curve',
                        'has_cp_curve']]
    if print_out:
        pd.set_option('display.max_rows', len(curves_df))
        print(curves_df)
        pd.reset_option('display.max_rows')
    return curves_df
