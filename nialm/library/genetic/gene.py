import random

class Gene(object):
	"""
		A Gene contains one number deciding what method will be used
		and a list of parameters for that method
	"""
	def __init__(self, method=None, methodlist=None):
		if method is None:
			self.method = random.choice(methodlist)
		else:
			self.method = method

		#generate list of random parameters, based on the parameter requirements set by the method
		self.params = {}
		for key,possibilities in self.method.param_list.iteritems():
			self.params.update({key : random.choice(possibilities)})

	def __repr__(self):
		print "Method: ",self.method
		print "Parameters: ",self.params
		return ""

	def mutate(self,mutation_rate):
		"""
			Calculates the chance for a mutation to happen, per parameter
			if so, change the parameters to a random value between its min and max

			Parameters
			----------
			mutation_rate : float
				value between 0 and 1 representing the percentual chance for a mutation
		"""

		for key,possibilities in self.method.param_list.iteritems():
			if random.random() < mutation_rate:
				self.params.update({key : random.choice(possibilities)})				

	def exec_method(self,data,tol):
		"""
			Executes the method and its parameters on the given data.
			Returns a result object

			Parameters
			----------
			data : object, list or dataframe containing the data
				specific to the problem at hand

			Returns
			-------
			result object, list or dataframe
				specific to the problem at hand
		"""

		return self.method.execute(params=self.params,data=data,tol=tol)	