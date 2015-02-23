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

	def execute(self,params,norm_data,der_data,tol):
		direction = params['direction']
		polarity = params['polarity']

		negatives = der_data[der_data < 0]
		positives = der_data[der_data > 0]

		if polarity == 'pos':
			for ix,val in positives[::direction].iteritems():
				for ix2,val2 in negatives[ix:].iteritems():
					if is_match(vala=val,valb=val2,tol=tol):
						return make_block_and_remove_from_signal(on_ix=ix,on_val=val,off_ix=ix2,off_val=val2,der_data=der_data,norm_data=norm_data)
		else:
			for ix2,val2 in negatives[::direction].iteritems():
				for ix,val in positives[0:ix2][::-1].iteritems():
					if is_match(vala=val,valb=val2,tol=tol):
						return make_block_and_remove_from_signal(on_ix=ix,on_val=val,off_ix=ix2,off_val=val2,der_data=der_data,norm_data=norm_data)

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
		polarity = {'polarity':['pos','neg']} #should the algorithm search for a negative or positive peak
		self.param_list.update(polarity) 

	def __repr__(self):
		return self.__name__

	def execute(self,params,der_data,norm_data,tol):
		direction = params['direction']
		polarity = params['polarity']

		negatives = der_data[der_data < 0]
		positives = der_data[der_data > 0]

		if polarity == 'neg':
			off = self.find_multiple(negatives,direction)
			if off:
				block = self.match_single_positive(positives,off,tol)
				if block and block.is_valid(norm_signal=norm_data):
					block.remove_block_from_signal(der_data=der_data,norm_data=norm_data)
					return block
				else:
					return None
			else:
				return None
		else:
			on = self.find_multiple(positives,direction)
			if on:
				block = self.match_single_negative(negatives,on,tol)
				if block and block.is_valid(norm_signal=norm_data):
					block.remove_block_from_signal(der_data=der_data,norm_data=norm_data)
					return block
				else:
					return None
			else: return None

	def find_multiple(self,series,direction=1):
	    for i in range(0,series.size)[::direction]:
	        if i==series.size-1: continue
	        if timediff(series,i) == 1:
	            event = Event(index=series.index[i],value=series[i])
	            event.add_point(wi e)
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
	            return block
	    return None

	def match_single_negative(self,series,event,tol):
	    target_value = event.get_total_value()
	    for ix,val in series[event.get_last_index():].iteritems():
	        if is_match(vala=target_value,valb=val,tol=tol):
	            off = Event(index=ix,value=val)
	            block = Block(event,off)
	            return block
	    return None

def make_block_and_remove_from_signal(on_ix,on_val,off_ix,off_val,der_data,norm_data):
	on = Event(index=on_ix,value=on_val)
	off = Event(index=off_ix,value=off_val)
	block = Block(on,off)
	if block.is_valid(norm_signal=norm_data):
		block.remove_block_from_signal(der_data=der_data,norm_data=norm_data)
		return block
	else:
		return None

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