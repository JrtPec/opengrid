import fluksoapi
import pandas as pd

class Flukso(object):
    """
        Object to contain a fluksometer and its sensors
    """
    def __init__(self,flukso_id,location='Leuven',gasenergy=10.):
        '''
            Default location is Leuven sinds the Houseprint does not supply a location

            Parameters
            ----------
            flukso_id: string
            location: string
            gasenergy: (default 10), Wh per Liter gas
        '''
        self.flukso_id = flukso_id
        
        self.location = location
        self.gasenergy = gasenergy
        
        self.sensors = []
        
    def add_sensor(self,sensor):
        '''
            Parameters
            ----------
            sensor: Sensor
        '''
        self.sensors.append(sensor)
        
    def has_sensors_by_type(self,sensortype):
        '''
            Parameters
            ----------
            sensortype: string ('gas','electricity','water')

            Returns
            -------
            bool
        '''
        temp = self.get_sensors_by_type(sensortype)
        if len(temp) > 0:
            return True
        else:
            return False
        
    def get_sensors_by_type(self,sensortype):
        '''
            Parameters
            ----------
            sensortype: string ('gas','electricity','water')

            Returns
            -------
            array of Sensor
        '''
        temp = []
        for sensor in self.sensors:
            if sensor.sensortype == sensortype:
                temp.append(sensor) 
        return temp
    
    def fetch_ts(self,sensortype,head=None,tail=None,tmposession=None):
        '''
            Parameters
            ----------
            sensortype: string ('gas','electricity','water')
            head: Pandas Timestamp, start of interval
            tail: Pandas Timestamp, end of interval
            tmposession: TMPO session object

            Returns
            -------
            Pandas DataSeries
        '''
        temp = self.get_sensors_by_type(sensortype)
        if len(temp) > 0:
            res = temp[0].fetch_ts(head,tail,tmposession)
        else:
            return None

        if res is None:
            return None

        if sensortype == "gas" and tmposession is not None:
            #TMPO returns gas data in Liters, so we have to multply by
            #the energy densitiy of the gas for that household to obtain Wh
            res = res*self.gasenergy

        return res

    def get_consumption_by_type(self,sensortype,head,tail,tmposession):
        """
            Add consumption for sensors of a certain Type

            Parameters
            ----------
            sensortype: string (electricity, gas, water)
            head: Pandas Timestamp
            tail: Pandas Timestamp
            tmposession: TMPO session object

            Returns
            -------
            float
        """

        sensors = self.get_sensors_by_type(sensortype)
        res = 0.
        for sensor in sensors:
            res += sensor.get_consumption(head,tail,tmposession)

        return res

    def get_sensorlist(self):
        """
            List of all sensor ids

            Returns
            -------
            array of strings
        """

        res = []
        for sensor in self.sensors:
            res.append(sensor.sensor_id)

        return res

class Sensor(object):
    """
        Flukso sensor object
    """
    def __init__(self,sensortype,sensor_id,token,function,gasenergy=10.):
        self.sensortype = sensortype
        self.sensor_id = sensor_id
        self.token = token
        self.function = function
        self.gasenergy = gasenergy
        
        if sensortype == 'water':
            self.unit = 'lperday'
        else:
            self.unit = 'watt'
        
    def fetch_ts(self,head=None,tail=None,tmposession=None):
        '''
            Return timeseries for sensor

            Parameters
            ----------
            head: Pandas Timestamp
            tail: Pandas Timestamp
            tmposession: TMPO Session object

            Returns
            -------
            Pandas DataSeries
        '''
        if tmposession is None:
            res = self.pull_api()
        else: #TMPO
            res = tmposession.series(self.sensor_id).ix[head:tail]
            if res.dropna().empty:
                return None
            res = dif_interp(res) #right now, this returns minute data only
            res = res
        return res
    
    def pull_api(self):
        '''
            Request Flukso.net for sensor data

            Returns
            -------
            Pandas DataSeries
        '''
        r = fluksoapi.pull_api(sensor = self.sensor_id,
                               token = self.token,
                               unit = self.unit,
                               resolution = 'day',
                               interval = 'decade')
        temp = fluksoapi.parse(r)
        temp = temp[temp != 'nan'].dropna()
        temp = temp.convert_objects(convert_numeric = True)
        temp.name = self.sensortype
        temp.index = pd.DatetimeIndex(temp.index).normalize()
        temp = temp.shift(periods=-1)
        temp = temp*24
        
        if temp.dropna().empty:
            return None
        else:
            return temp.dropna()

    def get_consumption(self,start,end,tmposession):
        """
            Get consumption for a given time period

            Parameters
            ----------
            start: Pandas Timestamp
            end: Pandas Timestamp
            tmposession: TMPO session object

            Returns
            -------
            float
        """
        try:
            ts = tmposession.series(self.sensor_id,head=start,tail=end)
        except:
            return 0
        else:
            if ts.dropna().empty:
                return 0
            else:
                first = ts[ts.first_valid_index()]
                last = ts[ts[::-1].first_valid_index()]
                res = last - first

        if self.sensortype == 'gas':
            res = res*self.gasenergy

        return res

def get_all_fluksos_from_houseprint(hp):
    """
        Parse houseprint and return flukso-objects

        Parameters
        ----------
        hp: Houseprint

        Returns
        -------
        Array of Flukso
    """

    #fetch all sensors from houseprint
    sensors = hp.get_all_fluksosensors()

    #make empty list
    Fluksos = []

    #loop all fluksos
    for flukso_id in sensors.keys():
        #create new flukso object
        new_flukso = Flukso(flukso_id = flukso_id)
        
        for sensor_id, s in sensors[flukso_id].items():
            if s is not None and s:
                #create new sensor object
                new_sensor = Sensor(sensortype = s['Type'],
                                sensor_id = s['Sensor'],
                                token = s['Token'],
                                function = s['Function']
                                )
                #add new sensor to flukso
                new_flukso.add_sensor(new_sensor)
                
        #append flukso object to list        
        Fluksos.append(new_flukso)

    return Fluksos

def dif_interp(ts):
    """
        Reformats Cumulative TMPO_data into interpolated and resampled time-data per minute

        Parameters
        ----------
        ts: pandas series

        Returns
        -------
        Pandas series
    """

    newindex = ts.resample('min').index
    ts = ts.reindex(ts.index + newindex)
    ts = ts.interpolate(method='time')
    ts = ts.reindex(newindex)
    ts = ts.diff()
    ts = ts*3600/60
    return ts