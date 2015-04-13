import pandas as pd
import numpy as np
from scipy import stats
import copy
import json

class Trend(object):
    """
        Abstract class for regression trends (linear or segmented)
    """

    #minimum value for an acceptible r squared
    r2_treshold = 0.75
    #maximum value for an acceptible CV(rmse)
    cvrmse_treshold = 0.2
    #minimum value for number of acceptible data points
    datasize_treshold = 10.
    #minimum range for temperatures
    hddrange_treshold = 15.
    
    def __init__(self,x,y,label=None):
        """
            Initialize the object

            Parameters
            ----------
            x,y: arrays with x and y values, must be same size!
            label: (optional, default=None), string describing the method used to filter the values
        """
        self.x = copy.deepcopy(x)
        self.y = copy.deepcopy(y)
        
        self.label = label

        #calculate r squared and CV(rmse)
        self.r2 = self._r2()
        self.cvrmse = self._cvrmse()
        
    def __gt__(self,other):
        """
            Override greater than (>) operator. Compare one trend with another. Returns True if self is better than other.

            Parameters
            ----------
            self: this trend object
            other: other trend object

            Returns
            -------
            Bool
        """
        
        #if one trend has valid r squared and cv(rsme), it is better than another
        if self.is_valid() and not other.is_valid():
            return True
        if not self.is_valid() and other.is_valid():
            return False
        
        #if both trends are valid or not valid, return the one with the highest score
        if self.get_reliability() > other.get_reliability():
            return True
        else:
            return False
        
    def _r2(self):
        """
            Calculate R Squared

            Returns
            -------
            float
        """
        res = np.corrcoef(self.y, self.p(self.x))[0,1] ** 2
        return res
    
    def _cvrmse(self):
        """
            Calculate CV(rmse)

            Returns
            -------
            float
        """
        #fit x values to ideal curve
        yfit = self.p(self.x)
        #subtract ideal curve from measurements and square the result
        ydif2 = [(a-b)**2 for a,b in zip(self.y,yfit)]
        #take the mean, square root, and divide by the average
        res = np.sqrt(np.mean(ydif2)) / np.average(self.y)
        return res
    
    def p(self,x):
        """
            Calculate the value on the trend line for given x-values

            Parameters
            ----------
            x: single number (float or int)
                OR iterable (array) of numbers

            Returns
            -------
            float if x is a single number
            array of floats if x is an iterable
        """

        #check if x is an iterable, if not: wrap in brackets
        if not hasattr(x, '__iter__'):
            temp_x = [x]
        else:
            temp_x = x
            
        #check if the trend object is a single trend, or made up from multiple trends
        if not hasattr(self, 'trends'):
            #if the trend object is a single trend,
            #return values according to formula y=ax+b, where a = slope and b = intercept
            res = [self.slope*val+self.intercept for val in temp_x]
        else:
            #if the trend object consists of more than one trend
            res = []
            #iterate values
            for val in temp_x:
                #check if value is before or after breakpoint
                if val <= self.bp:
                    r = self.trends[0].p(val)
                else:
                    r = self.trends[1].p(val)
                res.append(r)
            
        #if the result is a single number, return only the number and not the array
        if len(res) == 1:
            return res[0]
        else:
            return res
        
    def is_valid(self):
        """
            Check if r2 and cvrmse make a valid regression

            Returns
            -------
            Bool
        """
        return self.is_valid_r2() and self.is_valid_cvrmse()
        
    def is_valid_r2(self):
        """
            Check if r2 is above the treshold

            Returns
            -------
            Bool
        """
        return self.r2 > self.r2_treshold
        
    def is_valid_cvrmse(self):
        """
            Check if cvrmse is below the treshold

            Returns
            -------
            Bool
        """
        return self.cvrmse < self.cvrmse_treshold
    
    def get_output_data(self):
        """
            Order the data, put it in a pandas dataframe

            Returns
            -------
            Pandas DataFrame with columns 'gas' and 'hdd'
        """
        sorted_data = sorted(zip(self.x,self.y))
        x = [X for X,Y in sorted_data]
        y = [Y for X,Y in sorted_data]
    
        temp_x = pd.Series(x, name='hdd')
        temp_y = pd.Series(y, name='gas')
        return pd.concat([temp_x,temp_y],axis=1)
    
    def get_hddrange(self):
        """
            Calculate the range of degree days between 0 and the treshold

            Returns
            -------
            float: returns the treshold if the degree days go from
                    lower or equal than 0 to higher or equal to the treshold
        """
        return min(self.hddrange_treshold,max(self.x)) - max(0,min(self.x))
    
    def get_reliability(self):
        """
            Calculate a number that represents how reliable the trend is,
            based on the r2, cvrmse, the number of datapoints and the range of degree days

            Returns
            -------
            float: a value between 0 and 1. 1 meaning 100% reliable
        """
        rel_r2 = min(1,self.r2/self.r2_treshold)
        rel_cvrmse = min(1,self.cvrmse_treshold/self.cvrmse)
        rel_datasize = min(1,len(self.x)/self.datasize_treshold)
        rel_hddrange = min(1,self.get_hddrange()/self.hddrange_treshold)
        
        return 1 * rel_r2 * rel_cvrmse * rel_datasize * rel_hddrange
    
    def to_json(self):
        """
            Outputs all results in a JSON-formatted string

            Returns
            -------
            string: JSON-formatted, but without starting and trailing curly braces
        """

        hddrange = {"min":min(self.x),"max":max(self.x),"unit":"degC"}
    
        reliability = {"reliability factor":self.get_reliability(),
                   "regression method":self.label,
                   "r_squared":self.r2,
                   "cv(rmse)":self.cvrmse,
                   "used datapoints":len(self.x),
                   "degree day range":hddrange}
    
        slope = {"values":self.slope,"unit":"WattHoursperDegreeDay"}
        intercept = {"values":self.intercept,"unit":"WattHours","X0":self.p(0)}
        breakpoint = {"values":self.bp,"unit":"DegreeDays"}
        if self.bp is not None:
            function = '{a0:.0f}*x + {b0:.0f} for x <= {bp:.1f} | {a1:.0f}*x + {b1:.0f} for x > {bp:.1f}'.format(a0=self.slope[0],
                                                                                                            b0=self.intercept[0],
                                                                                                            a1=self.slope[1],
                                                                                                            b1=self.intercept[1],
                                                                                                            bp=self.bp)
        else:
            function = '{a:.0f}*x + {b:.0f}'.format(a=self.slope,b=self.intercept)
    
        kpis = {"slope":slope,
            "intercept":intercept, 
            "breakpoint":breakpoint,
            "reliability":reliability,
            "function":function}
        
        res = ""
        res += '"output data":{df:s}'.format(df=self.get_output_data().to_json())
        res += ',"kpis":{k:s}'.format(k=json.dumps(kpis))
        
        return res

class Linregress(Trend):
    """
        Subclass of Trend, single linear regression
    """
    def __init__(self,x,y,label=None):
        """
            Init Linear regression

            Parameters
            ----------
            x,y: arrays with x and y values, must be same size!
            label: (optional, default=None), string describing the method used to filter the values
        """
        self.slope, self.intercept, self.r_value, self.p_value, self.std_err = stats.linregress(x,y)
        
        self.bp = None
        
        #init superclass after liniar regression because it needs the slope and intercept
        super(Linregress, self).__init__(x,y,label)

class Segmented_Linregress(Trend):
    """
        Subclass of Trend, segmented linear regression
    """
    def __init__(self,x,y,label=None): 
        """
            Init Segmented regression

            Parameters
            ----------
            x,y: arrays with x and y values, must be same size!
            label: (optional, default=None), string describing the method used to filter the values
        """ 

        #put x and y in Pandas DataFrame
        temp_x = pd.Series(x, name='x')
        temp_y = pd.Series(y, name='y')
        self.df = pd.concat([temp_x,temp_y],axis=1)
        
        self.bp = self.calculate_breakpoint(x)
        #if a suitable breakpoint is found, finetune it and set trends, slope and intercept
        if self.bp is not None:
            self.trends = self.get_trends(self.bp)
            self._finetune_bp_trends(x)
            self.slope = {0:self.trends[0].slope,
                           1:self.trends[1].slope}
            self.intercept = {0:self.trends[0].intercept,
                               1:self.trends[1].intercept}
        #if no suitable breakpoint is found, use just a single linear regression
        else:
            self.trends = Linregress(x,y),Linregress(x,y)
            self.slope = self.trends[0].slope
            self.intercept = self.trends[0].intercept        
        
        #init superclass, which calculates r2 and cvrmse
        super(Segmented_Linregress, self).__init__(x,y,label)
    
    def calculate_intersect(self,trend_a,trend_b):
        """
            Calculate the point on the x-axis where two first degree functions intersect

            Parameters
            ----------
            trend_a, trend_b: Single Linear Regression objects

            Returns
            -------
            float
        """
        return (trend_a.intercept - trend_b.intercept) / (trend_b.slope - trend_a.slope)
    
    def _finetune_bp_trends(self, x):
        """
            Intersect the two trends, and recalculate them with the intersection as breakpoint,
            do this recursively untill no new trends are found

            Parameters
            ----------
            x: array of x values
        """

        for temp in range(100):
            #save old breakpoint, recalculate trends
            old = self.bp
            newtrends = self.get_trends(self.bp)
            #if no new trends are found, stop
            if newtrends is None:
                return
            #calculate intersection of new trends
            newintersect = self.calculate_intersect(newtrends[0],newtrends[1])
            
            #the slope of the first trend may not be bigger than the slope of the second trend
            #the intersection must lay in the range of the x-values
            if newtrends[0].slope < newtrends[1].slope and (min(x) < newintersect < max(x)):
                self.trends = newtrends
                self.bp = newintersect
            else:
                return

            #if the old intersection is the same as the new one, stop
            if old == self.bp:
                return
        
    def calculate_breakpoint(self, x):
        """
            Calculate the x-value after which a linear regression has the highest r2

            Parameters
            ----------
            x: array of x-values

            Returns
            -------
            int
        """
        #set start and end values of the loop
        lower = int(self.df['x'].min())
        #let the loop stop at 5, a breakpoint must be found before it
        upper = min(5,int(self.df['x'].max()))
        
        best_r2 = 0.
        best_bp = None

        for bp in range(lower,upper):
            try:
                trend_a,trend_b = self.get_trends(bp)
            except TypeError:
                continue
            #the slope of the second trend must be larger than the slope of the first trend
            if trend_a.slope > trend_b.slope: continue
            #the breakpoint must lay in the range of the x-values
            if not (min(x) < self.calculate_intersect(trend_a,trend_b) < max(x)): continue
            #r2 = trend_a.r2 + trend_b.r2

            r2 = trend_b.r2
            if r2 > best_r2:
                best_r2 = r2
                best_bp = bp

        return best_bp
    
    def get_trends(self,bp):
        """
            Return two linear regressions, one before and one after the breakpoint

            Parameters
            ----------
            bp: float, breakpoint

            Returns
            -------
            Trend,Trend
        """
        #split dataframe at breakpoint
        a = self.df[self.df['x'] <= bp]
        b = self.df[self.df['x'] > bp]
        
        #return none if empty
        if a.empty or b.empty:
            return None
        #we need at least 3 datapoints to make a linear regression
        if a.index.size < 3 or b.index.size < 3:
            return None
        
        #make linear regression objects
        trend_a = Linregress(x = a['x'].tolist(),
                               y = a['y'].tolist())
        trend_b = Linregress(x = b['x'].tolist(),
                               y = b['y'].tolist())
        
        return trend_a,trend_b