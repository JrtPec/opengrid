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

class Single_to_single(object):
	"""
		Detects a single-point event, matches with a single-point event
	"""
	def __init__(self):
		self.__name__ = "Single to single"
		self.param_list = {}

		direction = {'direction':[1,-1]} #possible directions in which to search for a peak. 1 is starting at the front, -1 at the back
		self.param_list.update(direction)
		polarity = {'polarity':['pos','neg']} #should the algorithm search for a negative or positive peak
		self.param_list.update(polarity)

	def __repr__(self):
		return self.__name__

	def execute(self,params,data,tol):
		direction = params['direction']
		polarity = params['polarity']

		negatives = data[data < 0]
		positives = data[data > 0]

		if polarity == 'pos':
			for ix,val in positives[::direction].iteritems():
				for ix2,val2 in negatives[ix:].iteritems():
					if is_match(vala=val,valb=val2,tol=tol):
						return make_block_and_remove_from_signal(on_ix=ix,on_val=val,off_ix=ix2,off_val=val2,data=data)
		else:
			for ix2,val2 in negatives[::direction].iteritems():
				for ix,val in positives[0:ix2][::-1].iteritems():
					if is_match(vala=val,valb=val2,tol=tol):
						return make_block_and_remove_from_signal(on_ix=ix,on_val=val,off_ix=ix2,off_val=val2,data=data)

		return None

	

def make_block_and_remove_from_signal(on_ix,on_val,off_ix,off_val,data):
	on = Event(index=on_ix,value=on_val)
	off = Event(index=off_ix,value=off_val)
	block = Block(on,off)
	block.remove_block_from_signal(data=data,diff=True)
	return block

def is_match(vala,valb,tol):
    if np.abs(vala + valb) <= vala * tol:
        return True
    else:
        return False

def get_methodlist():
	METHODLIST = []
	METHOD_A = Single_to_single()
	METHODLIST.append(METHOD_A)
	return METHODLIST