import pandas as pd
import numpy as np

class Block(object):
	"""
		A Block literally is a block of consumed power, characterized by an ON-event and an OFF-event
	"""
	def __init__(self, event1, event2):
		if event1.get_total_value > 0:
			self.on = event1
			self.off = event2
		else:
			self.on = event2
			self.off = event1

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
		print "Duration: ", self.duration, " s"
		print "Average power: ", self.avg_power, ' W'
		print "Total power: ", self.score, ' Wh'
		return ""

	def get_duration(self):
		"""
			Calculate the duration of the block

			Returns
			-------
			float : amount of seconds
		"""
		timedelta = self.df[::-1].first_valid_index() - self.df.first_valid_index()
		return timedelta / np.timedelta64(1,'s') + 1

	def get_score(self):
		"""
			Calculate the score of the block.
			This is the total cumulative power.

			Returns
			-------
			float
		"""
		return self.get_drawable().sum() /3600

	def get_avg_power(self):
		"""
			Calculate the average power of the block in W

			Returns
			-------
			float
				average power in W
		"""

		return self.get_drawable().mean()

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
		mean = norm_signal[self.df.first_valid_index()-pd.Timedelta(seconds=1):self.df[::-1].first_valid_index()].mean()
		minimum = norm_signal[self.on.get_last_index():self.off.get_first_index()-pd.Timedelta(seconds=1)].min()
		if self.avg_power > mean or np.isnan(minimum) or self.avg_power > minimum:
			return False
		else:
			return True
