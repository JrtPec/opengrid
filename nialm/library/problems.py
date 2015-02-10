import numpy as np
from block_detection_methods import get_methodlist

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
		self.df_diff_full = orig_data.diff()
		self.df_diff = self.df_diff_full[self.df_diff_full < 0].combine_first(self.df_diff_full[self.df_diff_full > 0])
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
		mean = self.df_orig.mean()
		begin = self.df_orig.first_valid_index()
		end = self.df_orig[::-1].first_valid_index()

		difference =  self.df_orig[end] - self.df_orig[begin] 
		
		timespan = (end - begin) / np.timedelta64(1,'s')

		return mean * timespan / 3600