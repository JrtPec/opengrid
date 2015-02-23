from event import Event
import numpy as np
import copy

def extract_events(data):
	events = []
	for i in range(0,data.size):
		if data[i] == 0 or np.isnan(data[i]): 
			continue
		else:
			event = Event(index=data.index[i],value=data[i])
			events.append(event)
			n = i
			while True:
				n += 1
				if n == data.size or data[n] == 0 or np.isnan(data[n]):
					break
				elif (data[n-1]<0) == (data[n]<0):
					event = copy.deepcopy(event)
					event.add_point(index=data.index[n],value=data[n])
					events.append(event)
				else:
					break
	return events

def match(events,i,tol=0.1):
	val1 = events[i].get_total_value()
	if val1 > 0:
		iterlist = events[i:]
	else:
		iterlist = events[0:i][::-1]

	for event in iterlist:
		val2 = event.get_total_value()
		if (val2<0) == (val1>0) and abs(val1+val2) <= abs(val1)*tol:
			return event

