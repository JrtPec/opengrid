import wundergroundapi as wg
import config
import copy
from handprint import Handprint
from modulation import Modulation_Analysis

c=config.Config()

wgkey = c.get('Wunderground', 'apikey')

def analyze_handprint(flukso):
    """
        Prepare data for fluksometers
        Run handprint analysis

        Parameters
        ----------
        flukso: Flukso

        Returns
        -------
        Handprint
    """

    #return None if flukso has no gas sensors
    if not flukso.has_sensors_by_type('gas'):
        return None
        
    #Gas and heating degree days are obligatory
    ts_gas = flukso.fetch_ts('gas')
    
    #If an empty timeseries is returned, continue
    if ts_gas is None:
        return None
    if ts_gas[ts_gas > 0].dropna().empty:
        return None
    
    start = ts_gas.index[0]
    end = ts_gas.index[-1]
    
    #ts_hdd = wg.get_stored_historic_dayaverage(key=wgkey,city=flukso.location,start=start,end=end,prop='all')['heatingdegreedays']
    temp = wg.get_hdd(wgkey=wgkey,location=flukso.location,start=start,end=end)
    ts_hdd = copy.deepcopy(temp)
    
    #Electricity and water are optional, but useful to refine the analysis
    ts_elec = flukso.fetch_ts('electricity')
    if ts_elec is not None and not ts_elec[start:end].dropna().empty:
        ts_elec = ts_elec[start:end]
    ts_water = flukso.fetch_ts('water')
    if ts_water is not None and not ts_water[start:end].dropna().empty:
        ts_water = ts_water[start:end]
    
    return Handprint(analysis_id = flukso.flukso_id,
                      gas = ts_gas,
                      hdd = ts_hdd,
                      elec = ts_elec,
                      water = ts_water)

def analyze_modulation(flukso,start,end,tmposession):
    """
        Prepare data for modulation analysis and Run

        Parameters
        ----------
        flukso: Flukso
        start: Pandas Timestamp
        end: Pandas Timestamp
        tmposession: TMPO session object
    """
    gas = flukso.fetch_ts(sensortype='gas',
                          head=start,
                          tail=end,
                          tmposession=tmposession)
    if gas is None:
        return None
    
    return Modulation_Analysis(analysis_id=flukso.flukso_id,
                               gas = gas)

def analyze_onoff(flukso,start,end,tmposession):
    """
        Prepare data and run analysis
        
        Parameters
        ----------
        flukso: Flukso
        start: Pandas Timestamp
        end: Pandas Timestamp
        tmposession: TMPO session object
        
        Returns
        -------
        Analysis object
    """
    
    gas = flukso.fetch_ts(sensortype='gas',
                          head=start,
                          tail=end,
                          tmposession=tmposession)
    if gas is None:
        return None
    
    return OnOff_Analysis(analysis_id=flukso.flukso_id,
                          gas = gas)