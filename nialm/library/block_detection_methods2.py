from event import Event
from block import Block
import numpy as np

class Single(object):
	def __init__(self):
		self.__name__ = "Single"
		self.param_list = {}

		direction = {'direction':[1,-1]} #possible directions in which to search for a peak. 1 is starting at the front, -1 at the back
		polarity = {'polarity':['pos','neg']} #should the algorithm search for a negative or positive peak
		matching_method = {'matching_method':['single','multiple']}

		self.param_list.update(direction)
		self.param_list.update(polarity)
		self.param_list.update(matching_method)

	def execute(self,params,norm_data,der_data,tol):
		direction = params['direction']
		polarity = params['polarity']
		matching_method = params['matching_method']

		if polarity == 'pos':
			series1 = der_data[der_data > 0]
			series2 = der_data[der_data < 0]
		else:
			series1 = der_data[der_data < 0]
			series2 = der_data[der_data > 0]

		for ix,val in series1[::direction].iteritems():
			event1 = Event(index=ix,value=val)
			if matching_method == 'single':
				event2 = match_single(series=series2,event=event1,polarity=polarity,tol=tol)
			else:
				event2 = match_multiple(series=series2,event=event1,polarity=polarity,tol=tol)
			if event2 is not None:
				if polarity == 'pos':
					block = Block(on=event1,off=event2)
				else:
					block = Block(off=event1,on=event2)
				if block.is_valid(norm_signal=norm_data):
					block.remove_block_from_signal(norm_data=norm_data,der_data=der_data)
					return block
				else:
					continue
			else:
				continue
		return None

def match_single(series,event,polarity,tol):
	if polarity == 'pos': #this means we're now looking for a negative peak
		series3 = series[event.get_last_index():]
	else:
		series3 = series[0:event.get_first_index()][::-1]

	event_val = event.get_total_value()
	for ix,val in series3.iteritems():
		if abs(val+event_val) <= abs(event_val)*tol:
			return Event(index=ix,value=val)
		else:
			continue
	return None

def match_multiple(series,event,polarity,tol):
	if polarity == 'pos':
		series3 = series[event.get_last_index():]
	else:
		series3 = series[0:event.get_first_index()][::-1]

	event_val = event.get_total_value()
	for i in range(0,series3.size-1):
		if timediff(series=series3,i=i) == 1:
			res_event = Event(index=series3.index[i],value=series3[i])
			res_event.add_point(index=series3.index[i+1],value=series3[i+1])
			if abs(res_event.get_total_value()+event_val) <= abs(event_val)*tol:
				return res_event
			else:
				n = i
				while True:
					n += 1
					if n == series3.size-1 or timediff(series=series3,i=n) != 1:
						break
					else:
						res_event.add_point(index=series3.index[n+1],value=series3[n+1])
						if abs(res_event.get_total_value()+event_val) < abs(event_val)*tol:
							return res_event
	return None

def timediff(series,i):
	try:
		res = abs(int((series.index[i+1] - series.index[i])/np.timedelta64(1,'s')))
	except:
		return 0
	else:
		return res

def get_methodlist():
	methodlist = []
	method_a = Single()
	methodlist.append(method_a)
	return methodlist
