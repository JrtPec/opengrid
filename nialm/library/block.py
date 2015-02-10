import pandas as pd
import numpy as np

class Block(object):
	"""
		A Block literally is a block of consumed power, characterized by an ON-event and an OFF-event
	"""
	def __init__(self, on, off):
		self.on = on
		self.off = off

		self.df = pd.Series(
			data=(self.on.values + self.off.values),
			index=(self.on.indexes + self.off.indexes)
			).sort_index()

	def __repr__(self):
		print "On: ", self.df.first_valid_index()
		print "Off: ", self.df[::-1].first_valid_index()
		print "Duration: ", self.get_duration()
		print "Power: ", self.get_avg_power()
		print "Score: ", self.get_score()
		return ""

	def get_duration(self):
		"""
			Calculate the duration of the block

			Returns
			-------
			float : amount of seconds
		"""
		timedelta = self.df[::-1].first_valid_index() - self.df.first_valid_index()
		return timedelta / np.timedelta64(1,'s')

	def get_score(self):
		"""
			Calculate the score of the block.
			This is the total cumulative power.

			Returns
			-------
			float
		"""
		return self.get_duration() * self.get_avg_power() / 3600

	def get_avg_power(self):
		"""
			Calculate the average power of the block in W

			Returns
			-------
			float
				average power in W
		"""
		total_on = abs(self.on.get_total_value())
		total_off = abs(self.off.get_total_value())

		return min(total_on,total_off)

	def remove_block_from_signal(self,data,diff=False):
		"""
			Remove the block from the signal

			Parameters
			----------
			data : Series
				Original signal with the block still present
			diff : bool (default=False)
				True => the original signal is a differential signal
				False => The original signal is a power signal #NOT IMPLEMENTED

			Returns
			-------
			Series, but make sure to do the drop inplace to avoid extra copies
		"""

		if diff == True:
			for index,value in self.df.iteritems():
				data.drop(index,inplace=True)
			return data
		else:
			#subtract the avg_power from all values along the duration of the block
			pass

	def get_drawable(self):
		"""
			Recreate the block with interpolated values so it can be plotted

			Returns
			-------
			Pandas Series
		"""	

		drawable = self.df.cumsum().resample('s').interpolate('zero')
		drawable[drawable.first_valid_index()-pd.Timedelta(seconds=1)] = 0.0
		return drawable.sort_index()


