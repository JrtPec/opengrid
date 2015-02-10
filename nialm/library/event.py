class Event(object):
	"""
		An Event is either a turn-on event or a turn-off event, characterized by at least one timestamp and a value
	"""
	def __init__(self,index=None,value=None):
		self.indexes = []
		self.values = []

		if index is not None and value is not None:
			self.add_point(index,value)

	def __repr__(self):
		print "Indexes: ", self.indexes
		print "Values: ", self.values
		return ""

	def __str__(self):
		return self.__repr__()

	def add_point(self,index,value):
		"""
			Add 1 data point to the event

			Parameters
			----------
			index : timestamp
			value : float
		"""

		#TODO: check if there isn't already an entry for the given index

		self.indexes.append(index)
		self.values.append(value)

	def get_total_value(self):
		"""
			Returns the sum of all values

			Returns
			-------
			float
		"""

		return sum(self.values)

	#FOLLOWING METHODS ARE DEPRECATED

	def get_first_index(self):
		"""
			Returns the fist index (in time)

			Returns
			-------
			timestamp
		"""

		return sorted(self.indexes)[0]

	def get_last_index(self):
		"""
			Returns the last index (in time)

			Returns
			-------
			timestamp
		"""

		return sorted(self.indexes)[::-1][0]