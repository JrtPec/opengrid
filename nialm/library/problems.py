import numpy as np
import pandas as pd
from block_detection_methods3 import extract_events as ee
from block_detection_methods2 import get_methodlist


"""
	A Problem represents a multivariable problem which can be
	optimized by using the genetic algorithm.
"""

class Disaggregation_problem(object):
	"""
		Container for a single sensor dataset problem
	"""

	def __init__(self,orig_data,tol=0.1,mutation_rate=0.05):
		self.df_orig = orig_data
		self.df_norm = self.remove_bias()
		self.df_diff_full = self.df_norm.diff()
		#self.df_diff = self.df_diff_full[self.df_diff_full < 0].combine_first(self.df_diff_full[self.df_diff_full > 0])
		self.events = ee(data=self.df_diff_full)
		self.tol = tol
		self.mutation_rate = mutation_rate
		self.methodlist = get_methodlist()

		try:
			self.score_ceiling = self.calc_score_ceiling()
		except:
			self.score_ceiling = None

	def __repr__(self):
		print "Sensor: ",self.df_orig.name
		print "Detection Ceiling: ",self.score_ceiling," Wh"
		return ""

	def calc_score_ceiling(self):
		"""
			Calculates the highest attainable score
		"""
		summ = self.df_norm.sum()
		'''
		begin = self.df_norm.first_valid_index()
		end = self.df_norm[::-1].first_valid_index()

		difference =  self.df_norm[end] - self.df_norm[begin] 
		
		timespan = (end - begin) / np.timedelta64(1,'s')

		return mean * timespan / 3600
		'''
		return summ/3600

	def remove_bias(self):
		bias1 = []
		bias2 = []
		for value in self.df_orig[self.df_orig.first_valid_index():]:
		    if not bias1:
		        low = value
		    elif value<low:
		        low = value
		    bias1.append(low)
		for value in self.df_orig[self.df_orig.first_valid_index():][::-1]:
		    if not bias2:
		        low = value
		    elif value<low:
		        low = value
		    bias2.append(low)
		    
		bias3 = []
		for a,b in zip(bias1,bias2[::-1]):
		    bias3.append(max(a,b))
		    
		bias = pd.Series(data=bias3,
		                 index=self.df_orig[self.df_orig.first_valid_index():].index)
		                 
		return self.df_orig - bias