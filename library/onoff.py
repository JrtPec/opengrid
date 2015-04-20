from opengrid.library.analysis import Analysis
import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json

class OnOff_Analysis(Analysis):
    """
        Analysis object
    """
    
    def __init__(self,gas,analysis_id=None):
        """
            Init

            Parameters
            ----------
            gas: Pandas series
            analysis_id: (optional), string
        """
        super(OnOff_Analysis, self).__init__(analysis_id)
        
        #init data
        self.df = copy.deepcopy(gas)
        
        self.onoff = self._filter_onoff(gas)
        self.ppd = self.points_per_day()
        
    def _filter_onoff(self,gas):
        """
            An on-event is characterized by a sudden positive change in gas consumption
            In this case this means that the derivative of the consumption is highter than 300

            Parameters
            ----------
            gas: Pandas Series

            Returns
            -------
            Pandas Series
        """
        temp = copy.deepcopy(gas)
        
        #take the derivative and filter retain values higher than 300
        temp = temp.diff()
        temp = temp[temp > 300]
        #resample back to minutes to add in NAN values
        temp = temp.resample('min')

        #if a non-NAN value is followed by another non-NAN value, discard it
        #otherwise we have on-events halfway a rising curve
        for ix,value in enumerate(temp):
            if np.isnan(value):continue
            if ix == temp.size-1 or np.isnan(temp[ix+1]):continue
            temp[ix] = np.float('NaN')
    
        #reindex the original data according to these filtered values
        newindex = temp.dropna().index
        res = copy.deepcopy(gas)
        res = res.reindex(newindex)
        res.name = 'onoff'
        return res
    
    def points_per_day(self):
        """
            Count the amount of on-events per day

            Returns
            -------
            Pandas Series
        """
        #create a dateindex for each day in the onoff data
        days = self.onoff.resample('d').index.normalize()
        values = []
        #loop all days and save the count of points
        for day in days:
            end = day + pd.Timedelta(days=1)
            ts_day = self.onoff[day:end]
            amount = ts_day.size
            values.append(amount)
        #Make a series and return
        return pd.Series(values,index=days,name='ppd')
    
    def number_of_days(self):
        """
            Number of days in the analysis

            Returns
            -------
            int
        """
        return (self.df.index[-1] - self.df.index[0]).days +1
    
    def to_plt(self):
        """
            Plot the gas consumption, the on-events and the amount of on-events per day

            Returns
            -------
            Matplotlib figure object
        """
        fig = plt.figure()
        plt.suptitle(self.analysis_id)
        ax1 = fig.add_subplot(111)
        plt.ylabel('Gas Consumption [W]')
        
        ax1.plot_date(self.df.index,self.df,'-',label='Gas consumption',alpha=0.5)
        ax1.plot_date(self.onoff.index,self.onoff,'.',color='g',label='On-event')
        
        plt.legend()
        plt.legend(loc='upper left')
        
        ax2 = ax1.twinx()
        label = 'On-Events per day\nMean: {m:.0f}'.format(m=self.ppd.mean())
        ax2.plot_date(self.ppd.index,self.ppd,'-',color='r',label=label)
        plt.ylabel('On events per day')
        
        plt.legend()
        
        return fig
    
    def to_json(self):
        """
            Output all in and output data, metadata and KPI's as json

            Returns
            -------
            JSON-formatted string
        """
        dates = {"start":str(self.df.index[0].date()),"end":str(self.df.index[-1].date())}
        metadata = {"number of days in analysis":self.number_of_days()}
        
        kpis = {"total on-events":self.onoff.size,
                "mean per day":int(self.ppd.mean()),
                "max day":self.ppd.max(),
                "min day":self.ppd.min(),
                }
                
        res = '{'
        res += '"analysis id":{id:s}'.format(id=json.dumps(self.analysis_id))
        res += ',"dates":{d:s}'.format(d=json.dumps(dates))
        res += ',"input data":{df:s}'.format(df=self.df.to_json())
        res += ',"On-Events":{df:s}'.format(df=self.onoff.to_json())
        res += ',"On-Events per day":{df:s}'.format(df=self.ppd.to_json())
        res += ',"metadata":{m:s}'.format(m=json.dumps(metadata))
        res += ',"kpis":{k:s}'.format(k=json.dumps(kpis))
        res += '}'
        
        return res