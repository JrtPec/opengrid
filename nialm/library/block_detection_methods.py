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

class Multiple_to_single(object):
	"""
		Detects a multiple point event, matches with a single-point event
	"""
	def __init__(self):
		self.__name__ = "Multiple to single"
		self.param_list = {}

		direction = {'direction':[1,-1]} #possible directions in which to search for a peak. 1 is starting at the front, -1 at the back
		self.param_list.update(direction)

	def __repr__(self):
		return self.__name__

	def execute(self,params,data,tol):
		direction = params['direction']


		negatives = data[data < 0]
		positives = data[data > 0]

		off = self.find_multiple(negatives,direction)
		if off:
			block = self.match_single_positive(positives,off,tol)
			if block:
				block.remove_block_from_signal(data=data,diff=True)
				return block
			else:
				return None
		else:
			return None

	def find_multiple(self,series,direction=1):
	    for i in range(0,series.size)[::direction]:
	        if i==series.size-1: continue
	        if timediff(series,i) == 1:
	            event = Event(index=series.index[i],value=series[i])
	            event.add_point(index=series.index[i+1],value=series[i+1])
	            while True:
	                i += 1
	                if i==series.size-1 or timediff(series,i) !=1:
	                    break
	                else:
	                    event.add_point(index=series.index[i+1],value=series[i+1])
	            return event
	    return None

	def match_single_positive(self,series,event,tol):
	    target_value = event.get_total_value()
	    for ix,val in series[0:event.get_first_index()][::-1].iteritems():
	        if is_match(vala=val,valb=target_value,tol=tol):
	            on = Event(index=ix,value=val)
	            block = Block(on,event)
	            #remove block from signal
	            return block
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

def timediff(series,i):
	    return int((series.index[i+1] - series.index[i])/np.timedelta64(1,'s'))

def get_methodlist():
	METHODLIST = []
	METHOD_A = Single_to_single()
	METHOD_B = Multiple_to_single()
	METHODLIST.append(METHOD_A)
	METHODLIST.append(METHOD_B)
	return METHODLIST