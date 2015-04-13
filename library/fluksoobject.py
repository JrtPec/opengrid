import fluksoapi
import pandas as pd

class Flukso(object):
    """
        Object to contain a fluksometer and its sensors
    """
    def __init__(self,flukso_id,location='Leuven'):
        '''
            Default location is Leuven sinds the Houseprint does not supply a location

            Parameters
            ----------
            flukso_id: string
            location: string
        '''
        self.flukso_id = flukso_id
        
        self.location = location
        
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
    
    def fetch_ts(self,sensortype):
        '''
            Parameters
            ----------
            sensortype: string ('gas','electricity','water')

            Returns
            -------
            Pandas DataSeries
        '''
        temp = self.get_sensors_by_type(sensortype)
        if len(temp) > 0:
            return temp[0].fetch_ts()
        else:
            return None

class Sensor(object):
    """
        Flukso sensor object
    """
    def __init__(self,sensortype,sensor_id,token,function):
        self.sensortype = sensortype
        self.sensor_id = sensor_id
        self.token = token
        self.function = function
        
        if sensortype == 'water':
            self.unit = 'lperday'
        else:
            self.unit = 'watt'
        
    def fetch_ts(self):
        '''
            Return timeseries for sensor

            Returns
            -------
            Pandas DataSeries
        '''
        if not hasattr(self,'ts'):
            self.ts = self.pull_api()
        return self.ts
    
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