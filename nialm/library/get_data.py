import os, sys, inspect
import numpy as np

script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# add the path to opengrid to sys.path
sys.path.append(os.path.join(script_dir, os.pardir, os.pardir,'..'))

from opengrid.library import houseprint
from opengrid.library import fluksoapi
from opengrid.library import config

def get_flukso_data(start,end,sensortype='electricity',sensor=None):
	"""
	Opens a connection to Flukso, downloads raw data for the given type and time.
	Transforms the cumulative data into its differential.

	Parameters
	__________

	start : Timestamp
	end : Timestamp
	sensortype = {None, 'gas', 'electricity', 'water'}, optional
		defaults to electricity
	sensor : sensor number (hex), optional
		(not implemented), if this value is set, only data for that sensor is returned

	Returns
	-------

	Pandas dataframe containing sensor data change over time
	"""

	c=config.Config()

	# find tmpo
	path_to_tmpo = c.get('tmpo','folder')
	if not os.path.exists(path_to_tmpo):
		raise IOError("Provide your path to the tmpo folder in your config.ini file")
	else:
		sys.path.append(path_to_tmpo)
		import tmpo

	#load housprint file
	try:
		hp = houseprint.load_houseprint_from_file('hp_anonymous.pkl')
	except:
		raise IOError("Houseprint file not found")

	#load tmpo session
	tmpos = tmpo.Session()
	tmpos.debug = False

	tmpo_sensors = [sid for (sid,) in tmpos.dbcur.execute(tmpo.SQL_SENSOR_ALL)]
	elec_sensors = set(tmpo_sensors) & set(hp.get_sensors_by_type(sensortype))
	print "{} electricity sensors".format(len(elec_sensors))
	tmpos.sync()

	#Load dataframe for selected sensors end timing
	df = tmpos.dataframe(elec_sensors,head=start,tail=end)

	#Re-index and interpolate
	df_interpol = clean_tmpo(df)

	#Take the differential
	df_diff = df_interpol.diff()*3600 #1Wh per second = 3600W, in kW

	#Filter
	df_diff_filtered = filter_diff(df_diff)

	return df_diff_filtered

def clean_tmpo(df):
	"""
	Takes a dataframe from TMPO, re-indexes per second and interpolates.

	Parameters
	----------

	df = pandas dataframe
		Dataframe containing raw data from TMPO

	Returns
	_______
	re-indexed and interpolated pandas dataframe
	"""

	#Resample only the index first, per second. This is to avoid (more) quantization errors on the time axis.
	newindex = df.resample('s').index
	#Add both the old time index and the new time index together
	df_interpol = df.reindex(df.index + newindex)
	#Interpolate data
	df_interpol = df_interpol.interpolate(method='time')

	return df_interpol

def filter_diff(df_diff):
	"""
	Removes single sample spikes which are caused by quantization errors

	Parameters
	----------

	df_diff = pandas dataframe
		Dataframe containing a continuous power signal

	Returns
	-------
	filtered dataframe

	"""
	df_diff_filtered = df_diff.copy()
	for sensor in df_diff_filtered:
    
	    #Add all values to list
	    values = df_diff[sensor].tolist()

	    #Compare each value with the previous and next value
	    #If the current value is not between its two neighbors, it is a spike.
	    #Loop to remove bigger spikes that aren't fully deleted
	    while True:
	        peakcount = 0
	        for n in range(1,len(values)-1):
	            if values[n-1] <= values[n] <= values[n+1] or values[n-1] >= values[n] >= values[n+1]:
	                pass
	            elif np.isnan(values[n-1]) or np.isnan(values[n+1]):
	                pass
	            else:
	                values[n] = (values[n-1]+values[n+1])/2
	                peakcount += 1
	        if peakcount == 0:
	            break

	    #Overwrite dataframe with new values
		df_diff_filtered[sensor] = values

	return df_diff_filtered	