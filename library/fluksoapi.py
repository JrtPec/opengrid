# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 15:31:36 2013 by Carlos Dierckxsens

"""
import sys
import pandas as pd
import requests
import os
import pytz
import re
import zipfile
import glob
import time

def save_csv(Ts, csvpath=None, fileNamePrefix=''):
    """
    Save the TimeSeries or DataFrame to csv with specified name
    
    Parameters
    ----------
    Ts : pandas Timeseries or Dataframe
    csvpath : path, default=None
        Folder where the csv will be saved. Defaults to os.getcwd()
    fileNamePrefix = string, default=''
        Name prefix for the csv, usually FLxxxxxxx_sensorid
        
    Returns
    -------
    csv : abspath
        Absolute path to the saved file
    """
    
   
    # save to file
    if csvpath is None:
        csvpath = os.getcwd()
    s = Ts.index[0].strftime(format="%Y-%m-%d_%H-%M-%S")
    e = Ts.index[-1].strftime(format="%Y-%m-%d_%H-%M-%S")
        
    csv = os.path.join(csvpath, fileNamePrefix + '_FROM_' + s + 
                                    '_TO_' + e + '.csv')
    
    Ts.to_csv(csv, header=False)
    return csv    

   
def save_hdf(df, path=None, prefix=''):
    """
    Save the TimeSeries or DataFrame to hdf with specified name
    
    Parameters
    ----------
    ts : pandas Timeseries or Dataframe
    path : path, default=None
        Folder where the hdf will be saved. Defaults to os.getcwd()
    prefix = string, default=''
        Name prefix for the hdf, usually FLxxxxxxx_sensorid
        
    Returns
    -------
    hdf : abspath
        Absolute path to the saved file
    """
    
   
    # save to file
    path = path or os.getcwd()
    s = df.index[0].strftime(format="%Y-%m-%d_%H-%M-%S")
    e = df.index[-1].strftime(format="%Y-%m-%d_%H-%M-%S")
    hdf = os.path.join(path, prefix + '_FROM_' + s + '_TO_' + e + '.hdf')
    
    df.to_hdf(hdf, 'df', mode='w')
    return hdf

   
def load_file(path):
    """
    Load a previously saved csv or hdf file into a dataframe and return it.
    
    Parameters
    ----------
    path : path
        Path to a csv or hdf file.  Filename should be something like fluksoID_sensor_FROM_x_to_y.csv

    Returns
    -------
    df : pandas.DataFrame
        The dataframe will have a DatetimeIndex with UTC timezone.  The 
        column will be the sensor-ID, extracted from the csv filename. If invalid filename is given, an empty dataframe will be returned.
    
    """
    if len(path) == 0 or 'FROM' not in path:
        return pd.DataFrame()
    
    if '.csv' in path:
        df = pd.read_csv(path, index_col = 0, header=None, parse_dates=True)
        # Convert the index to a pandas DateTimeIndex 
        df.index = pd.to_datetime(df.index)
        df.index = df.index.tz_localize('UTC')
        df.columns = [path.split('_')[-7]]
    elif '.hdf' in path:
        df = pd.read_hdf(path, 'df')
    return df


def load_sensor(folder, sensor, dt_start=None, dt_end=None):
    files = glob.glob(os.path.join(folder, '*' + sensor + '*'))
    if len(files) == 0:
        # if no valid (unhidden) files are found, raise a ValueError.
        raise ValueError('No files found for sensor {} in {}'.format(sensor, folder))
    print("About to combine {} files for sensor {}".format(len(files), sensor))
    dfs = [load_file(f) for f in files]
    combination = dfs[0]
    for df in dfs[1:]:
        combination = combination.combine_first(df)
    combination = combination.ix[dt_start:dt_end]
    return combination


def consolidate_sensor(folder, sensor, test=False):
    """
    Merge all csv and/or hdf files for a given sensor into a single hdf file
    
    - the given sensor
    - and the given day
    into a single hdf file
    
    Parameters
    ----------
    folder : path
        Folder containing the csv files
    sensor : hex
        Sensor for which files are to be consolidated
    remove_temp : (optional) Boolean, default=False
        If True, only the resulting consolidated hdf is kept, the files that
        have been consolidated are deleted.
        
    Returns
    -------
    hdf : path of the resulting hdf file
    
    """
		
    # List all files (ABSPATH) for the given sensor in the given path, without hidden files			
    # glob.glob() is equivalent to os.listdir(folder) without the hidden files (start with '.') 
    # and returned as absolute paths
    files = glob.glob(os.path.join(folder, '*' + sensor + '*'))
    if len(files) == 0:
        # if no valid (unhidden) files are found, raise a ValueError.
        raise ValueError('No files found for sensor {} in {}'.format(sensor, folder))
    elif len(files) == 1:
        print("One file found and retained for sensor {}".format(sensor))
        return files[0]
    else:
        combination = load_sensor(folder, sensor)
        if not test:
            for f in files:
                os.remove(os.path.join(folder, f))
        print("Removed the {} temporary files".format(len(files)))
        
        # Obtain the new filename prefix, something like FX12345678_sensorid
        # the _FROM....hdf will be added by the save_hdf method
        prefix = files[-1].split('_FROM')[0]
        hdf = save_hdf(combination, path=folder, prefix=prefix)
        print('Saved ', hdf)
        return hdf


def consolidate_folder(folder):
    
    sensor_set = {x.split('_')[1] for x in glob.glob(os.path.join(folder, '*'))}
    print 'About to consolidate {} sensors'.format(len(sensor_set))
    for sensor in sensor_set:
        consolidate_sensor(folder, sensor)
    

def synchronize(folder, unzip=True, consolidate=True):
    """Download the latest zip-files from the opengrid droplet, unzip and consolidate.
    
    The files will be stored in folder/zip and unzipped and 
    consolidated into folder/csv
    
    Parameters
    ----------
    
    folder : path
        The *data* folder, containing subfolders *zip* and *csv*
    unzip : [True]/False
        If True, unzip the downloaded files to folder/csv
    consolidate : [True]/False
        If True, all csv files in folder/csv will be consolidated to a 
        single file per sensor
    
    Notes
    -----
    
    This will only unzip the downloaded files and then consolidate all
    csv files in the csv folder.  If you want to rebuild the consolidated
    csv from all available data you can either delete all zip files and 
    run this function or run _unzip(folder, consolidate=True) on the 
    data folder.
        
    """
    t0 = time.time()
    if not os.path.exists(folder):
        raise IOError("Provide your path to the data folder where a zip and csv subfolder will be created.")
    from opengrid.library import config
    # Get the pwd; start from the path of this current file 
    c = config.Config()
    pwd = c.get('opengrid_server', 'password')
    host = c.get('opengrid_server','host')
    port = c.get('opengrid_server','port')
    user = c.get('opengrid_server','user')
    URL = "".join(['http://',host,':',port,'/'])
    
    # create a session to the private opengrid webserver
    session = requests.Session()
    session.auth = (user, pwd)
    resp = session.get(URL)
    
    # make a list of all zipfiles
    pattern = '("[0-9]{8}.zip")' 
    zipfiles = re.findall(pattern, resp.content)
    zipfiles = [x.strip('"') for x in zipfiles]
    zipfiles.append('all_data_till_20140711.zip')
    
    zipfolder = os.path.join(folder, 'zip')    
    csvfolder = os.path.join(folder, 'csv')

    # create the folders if they don't exist
    for fldr in [zipfolder, csvfolder]:
        if not os.path.exists(fldr):
            os.mkdir(fldr)
    
    downloadfiles = [] # these are the successfully downloaded files       
    for f in zipfiles:
        # download the file to zipfolder if it does not yet exist
        if not os.path.exists(os.path.join(zipfolder, f)):
            print("Downloading {}".format(f))       
            with open(os.path.join(zipfolder, f), 'wb') as handle:
                response = session.get('http://95.85.34.168:8080/' + f, stream=True)
        
                if not response.ok:
                    raise IOError('Something went wrong in downloading of {}'.format(f))
        
                for block in response.iter_content(1024):
                    if not block:
                        break
                    handle.write(block)
            downloadfiles.append(f)
            
    t1 = time.time()
    # Now unzip and/or consolidate
    if unzip:
        _unzip(folder, downloadfiles)
    t2 = time.time()
    if consolidate:
        consolidate_folder(csvfolder)
    t3 = time.time()
    print 'Download time: {} s'.format(t1-t0)
    print 'Unzip time: {} s'.format(t2-t1)
    print 'Consolidate time: {} s'.format(t3-t1)
    print 'Total time: {} s'.format(t3-t0)
        

def _unzip(folder, files='all'):
    """
    Unzip zip files from folder/zip to folder/csv
        
    Parameters
    ----------
    
    folder : path
        The *data* folder, containing subfolders *zip* and *csv*
    files = 'all' (default) or list of files
        Unzip only these files
    
    """

    zipfolder = os.path.join(folder, 'zip')    
    csvfolder = os.path.join(folder, 'csv')

    # create the folders if they don't exist
    for fldr in [zipfolder, csvfolder]:
        if not os.path.exists(fldr):
            os.mkdir(fldr)

    if files == 'all':
        files = os.listdir(zipfolder)
    print 'About to unzip {} files'.format(len(files))
    badfiles = []
    
    for f in files:
        # now unzip to zipfolder
        try:       
            z = zipfile.ZipFile(os.path.join(zipfolder, f), 'r')
            z.extractall(path=csvfolder)
        except:
            badfiles.append(f)
            pass
    
    if badfiles:
        print("Could not unzip these files:")
        for f in badfiles:
            print f
  
    
def update_tmpo(tmposession, hp):
    """
    Update the tmpo database with all sensors from a houseprint object.
    This does NOT synchronize the data, only loads the sensors.  
    
    Parameters
    ----------
    tmposession : tmpo.Session object
    hp : a Houseprint object
    
    Returns
    -------
    tmposession : return the tmpo.Session
    """
    
    # get a list of all sensors in the hp.  The list contains tuples (sensor,token)
    sensors_tokens = hp.get_all_sensors(tokens=True)
    for s,t in sensors_tokens:
        tmposession.add(s,t)

    print("This tmpo session was updated with in total {} sensors".format(len(sensors_tokens)))
    return tmposession
    
    
def load_tmpo(tmposession, sensors, start=None, end=None):
    """
    Load data from one or more sensors into a pandas DataFrame
    
    Parameters
    ----------
    tmposession : tmpo.Session object
        tmpo session
    sensors : Str or List
        String: single sensor to be loaded
        List: list of sensors to be loaded
    start, end : Datetime, float, int, string or pandas Timestamp (default=None)
        Anything that can be parsed into a pandas.Timestamp
        If start is None, load all available data
        If end is None, end is the current time
    
    Returns
    -------
    df : pandas DataFrame
        DataFrame with DatetimeIndex and sensor-ids as columname.  If only a 
        single sensor is given, return a DataFrame instead of a Timeseries.

    Raises
    ------
    If no data is found, do not return an empty dataframe but raise
    a ValueError.
    
    """

    if isinstance(sensors, str):
        sensors = [sensors]
    
    # convert start and end to epoch
    if start is None:
        startepoch = 0
    else:
        # use parse_date to convert to pd.Timestamp and from there to POSIX
        startepoch = _parse_date(start).value/1e9
        
        # convert start and end to epoch
    if end is None:
        endepoch = sys.maxint
    else:
        # use parse_date to convert to pd.Timestamp and from there to POSIX
        endepoch = _parse_date(end).value/1e9

    # get list of timeseries    
    dfs = []    
    for s in sensors:
        try:        
            ts = tmposession.series(sid=s, head=startepoch, tail=endepoch)
        except Exception as e:
            print("No tmpo data for sensor {}".format(s))
        else:
            if len(ts) > 0:
                dfs.append(ts)
    
    df = pd.concat(dfs, axis=1)
    # convert POSIX timestamp (seconds since epoch) to DatetimeIndex    
    df.index = pd.to_datetime((df.index.values*1e9).astype(int))    
    return df
    
    
def load(path_csv, sensors, start=None, end=None):
    """
    Load data from one or more sensors into a pandas DataFrame.  
    
    Parameters
    ----------
    path_csv : str
        Folder containing the csv files with data to be loaded
    sensors : str or list of str
        Sensors to be loaded
    start, end : Datetime, float, int, string or pandas Timestamp, optional
        Anything that can be parsed into a pandas.Timestamp
        If start and end are not provided, all available data is loaded.
    
    Returns
    -------
    df : pandas DataFrame
        DataFrame with DatetimeIndex and sensor ids as column names.

    Raises
    ------
    If no single sensor is found, do not return an empty dataframe but raise
    a ValueError. Not implemented.
    
    Notes
    -----
    Currently, this function only calls ``load_sensor`` (csv and/or hdf files).
    Ultimately, it will first call ``load_tmpo`` and if the tmpo database does
    not contain all historic data (depending on start), it will also call 
    ``load_sensor``. Not implemented.
    
    """
    if isinstance(sensors, str):
        sensors = [sensors]
    
    dataframes = [load_sensor(path_csv, sensor, start, end) for sensor in sensors]
    df = pd.concat(dataframes, axis=1)
    df.index = df.index.tz_convert(pytz.timezone('Europe/Brussels'))
    
    print('{} sensors loaded'.format(len(df.columns)))
    df = df.dropna(axis=1, how='all')
    print('{} sensors retained'.format(len(df.columns)))
    print "Size of dataframe: {}".format(df.shape)

    return df


def _parse_date(d):
    """
    Return a pandas.Timestamp if possible.  
    
    Parameters
    ----------
    d : Datetime, float, int, string or pandas Timestamp
        Anything that can be parsed into a pandas.Timestamp
        
    Returns
    -------
    pts : pandas.Timestamp
    
    Raises
    ------
    ValueError if it was not possible to create a pandas.Timestamp
    """
    
    if isinstance(d, float) or isinstance(d, int):
        # we have a POSIX timestamp IN SECONDS.
        pts = pd.Timestamp(d, unit='s')
        return pts
        
    try:
        pts = pd.Timestamp(d)
    except:
        raise ValueError("{} cannot be parsed into a pandas.Timestamp".format(d))
    else:
        return pts
