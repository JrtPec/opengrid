import numpy as np
from event import *
from block import *

"""
	Every detection method has to meet following specifications:

		It has to be a class
		It has to have these variables:
			param_list
				A list of all parameters for the method, with a list per parameter containing all options
		It has to implement these methods:
			execute(self,params,data):
				params : list with Param objects
				data : pandas DataFrame
				tol : float
					tolerance
				return Block object, None if detection fails
"""

class Negative_edge_detection(object):
	def __init__(self):
		self.__name__ = "Negative Edge Detection"
		self.param_list = {}

		direction = {'direction':[1,-1]} #possible directions in which to search for a peak. 1 is starting at the front, -1 at the back
		self.param_list.update(direction)

	def __repr__(self):
		return self.__name__

	def execute(self,params,data,tol):
		"""
			Detect a negative spike, match an according positive
		"""
		direction = params['direction']

		negatives = data[data < 0][::direction]
		positives = data[data > 0]

		for neg_ix,neg_val in negatives.iteritems():
			for pos_ix,pos_val in positives[0:neg_ix][::-1].iteritems():
				if is_match(neg_val,pos_val,tol):
					off = Event(index=neg_ix,value=neg_val)
					on = Event(index=pos_ix,value=pos_val)
					block = Block(on,off)
					block.remove_block_from_signal(data=data,diff=True)
					return block

		return None

def is_match(neg,pos,tol):
    if np.abs(neg + pos) <= pos * tol:
        return True
    else:
        return False

def get_methodlist():
	METHODLIST = []
	METHOD_A = Negative_edge_detection()
	METHODLIST.append(METHOD_A)
	return METHODLIST