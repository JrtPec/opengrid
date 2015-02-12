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

		self.duration = self.get_duration()
		self.avg_power = self.get_avg_power()
		self.score = self.get_score()

	def __repr__(self):
		print "On: ", self.df.first_valid_index()
		print "Off: ", self.df[::-1].first_valid_index()
		print "Duration: ", self.duration
		print "Power: ", self.avg_power
		print "Score: ", self.score
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
		return self.duration * self.avg_power / 3600

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

	def remove_block_from_signal(self,norm_data=None,der_data=None):
		"""
			Remove the block from the signal

			Parameters
			----------
			norm_data : DataFrame
				normalised data for the individual
			der_data : DataFrame
				first derivative of the normalised data

			Returns
			-------
			Nothing, make sure to do the drop inplace to avoid extra copies
		"""

		if der_data is not None:
			for index,value in self.df.iteritems():
				der_data.drop(index,inplace=True) #maybe test simple subtraction to speed up process
		if norm_data is not None:
			block = self.df.cumsum().resample('s').interpolate('zero')
			for index,value in block.iteritems():
				norm_data[index] -= abs(value)
		return True
			

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

	def is_valid(self,norm_signal):
		mean = norm_signal[self.df.first_valid_index():self.df[::-1].first_valid_index()].mean()
		if mean < self.avg_power:
			return False
		else:
			return True
