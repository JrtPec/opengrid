from analysis import Analysis
import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json

class Modulation_Analysis(Analysis):
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
        super(Modulation_Analysis, self).__init__(analysis_id)
        
        #init data
        self.df = copy.deepcopy(gas)
        
        #calculate mods
        self.mods = self._split_modulations(gas)
        #filter modulations under treshold gas usage
        self.drop_mods_under_tresh()
        #filter mods under duation treshold
        self.drop_short_mods()
        
    def _split_modulations(self,gas):
        """
            Takes the data and returns a list of modulations

            Parameters
            ----------
            gas: Pandas series

            Returns
            -------
            array of Modulation objects
        """
        #filter the data so that only moments when modulations occur remain
        df_temp = self._prepare_data(gas)
        
        '''
                _prepare_data returns a series with modulations,
                seperated by NAN values.
                This method finds values that follow each other without NAN,
                and dumps the corresponding original data into a modulation object.
        '''
        temp = []
        mod = None
        for ix, val in enumerate(df_temp):
            if np.isnan(val):
                if mod is not None:
                    end = df_temp.index[ix-1]
                    mod.set_series(copy.deepcopy(self.df[begin:end]))
                    temp.append(mod)
                mod = None
                continue
            elif mod is None:
                mod = Modulation()
                begin = df_temp.index[ix]
                
        return temp
        
    def _prepare_data(self,gas):
        """
            Filter data so that only modulations remain

            Modulations are characterized by a slowly descending curve.
            This means the derivative of the curve is a small negative number (between 0 and -1500 in this case)

            Parameters
            ----------
            gas: Pandas series

            Returns
            -------
            Pandas series
        """
        #First take the average in 5 minutes
        df_temp = pd.rolling_mean(gas,5)
        #take the derivative
        df_temp = df_temp.diff()
        #filter values between 0 and -1500
        df_temp = df_temp[0 > df_temp]
        df_temp = df_temp[-1500 < df_temp]
        #Average again
        df_temp = pd.rolling_mean(df_temp,5)
        #resample to add NAN values in between
        df_temp = df_temp.resample('min')
        return df_temp
    
    def number_of_days(self):
        """
            Amount of days in the analysis

            Returns
            -------
            int
        """
        return (self.df.index[-1] - self.df.index[0]).days +1
    
    def is_modulating(self):
        """
            Are modulations detected or not

            Returns
            -------
            bool
        """
        return len(self.mods) > 0
    
    def get_total_minutes(self):
        """
            Total minutes of modulation behaviour in analysis

            Returns
            -------
            int
        """
        minutes = 0
        for mod in self.mods:
            minutes += mod.get_minutes()
        return minutes
    
    def minutes_per_day(self):
        """
            Minutes of modulation behaviour per day

            Returns
            -------
            int
        """
        return self.get_total_minutes()/self.number_of_days()
    
    def get_total_consumption(self):
        """
            Amount of gas consumption during modulation behaviour

            Returns
            -------
            float
        """
        consumption = 0.
        for mod in self.mods:
            consumption += mod.get_consumption()
        return consumption
    
    def consumption_per_day(self):
        """
            Amout of gas consumption during modulation behaviour, per day

            Returns
            -------
            float
        """
        return self.get_total_consumption()/self.number_of_days()
    
    def drop_mods_under_tresh(self,tresh=7000):
        """
            Drops detected modulations that happen under a certain treshold value

            Parameters
            ----------
            tresh: int, default=7000
        """
        for mod in set(self.mods):
            mod.drop_low_vals(tresh)
            if mod.series.empty:
                self.mods.remove(mod)
                
    def drop_short_mods(self,tresh=5):
        """
            Drops detected modulations that are under a certain duration

            Parameters
            ----------
            tresh: int, default=5, minutes
        """
        for mod in set(self.mods):
            if mod.get_minutes() < tresh:
                self.mods.remove(mod)
                
    def get_series(self):
        """
            Returns all modulations in the analysis as a Pandas Series

            Returns
            -------
            Pandas Series
        """
        ts = None
        for mod in self.mods:
            if ts is None:
                ts = mod.series
            else:
                ts = ts.add(mod.series, fill_value=0)
        return ts
    
    def number_of_modulations(self):
        """
            Number of detected modulations

            Returns
            -------
            int
        """
        return len(self.mods)
    
    def modulations_per_day(self):
        """
            Number of detected modulations per day

            Returns
            -------
            int
        """
        return self.number_of_modulations()/self.number_of_days()
    
    def avg_duration(self):
        """
            Duration of the average modulation in the analysis

            Returns
            -------
            float
        """
        if self.number_of_modulations() == 0:
            return 0
        else:
            return self.get_total_minutes() / self.number_of_modulations()
        
    def avg_consumption(self):
        """
            Average Gas consumption of a modulation in the analysis

            Returns
            -------
            float
        """
        if self.number_of_modulations() == 0:
            return 0.
        else:
            return self.get_total_consumption() / self.number_of_modulations()
    
    def longest_mod(self):
        """
            Modulation with the largest duration in the analysis

            Returns
            -------
            Modulation
        """
        longest = Modulation()
        for mod in self.mods:
            if mod.get_minutes() > longest.get_minutes():
                longest = mod
        return longest
    
    def largest_mod(self):
        """
            Modulation with the largest gas consumption in the analysis

            Returns
            -------
            Modulation
        """
        largest = Modulation()
        for mod in self.mods:
            if mod.get_consumption() > largest.get_consumption():
                largest = mod
        return largest
    
    def largest_delta(self):
        """
            Modulation with the largest difference in power between begin and end

            Returns
            -------
            Modulation
        """
        largest = Modulation()
        for mod in self.mods:
            if mod.delta() > largest.delta():
                largest = mod
        return largest
    
    def avg_delta(self):
        """
            Average difference in power between begin and end of a modulation

            Returns
            -------
            float
        """
        if self.number_of_modulations() == 0:
            return 0.
        else:
            delta = 0.
            for mod in self.mods:
                delta += mod.delta()
            return delta / self.number_of_modulations()
        
    def to_plt(self):
        """
            Draws a plot of the gas consumption and highlights the modulations

            Returns
            -------
            Matplotlib object
        """
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
    
        ax1.plot_date(self.df.index,self.df,'-')
        try:
            ax1.plot_date(self.get_series().index,self.get_series(),'.',color='r')
        except:
            pass
        plt.ylabel('Gas Consumption [W]')
        plt.suptitle(self.analysis_id)
        return fig
    
    def to_json(self):
        '''
            Output KPI's, metadata, in- and output data as JSON

            Returns
            -------
            JSON-formatted string
        '''
        
        dates = {"start":str(self.df.index[0].date()),"end":str(self.df.index[-1].date())}
        metadata = {"number of days in analysis":self.number_of_days()}
        
        duration = {"total":self.get_total_minutes(),
                    "average":self.avg_duration(),
                    "average per day":self.minutes_per_day(),
                    "longest":self.longest_mod().get_minutes(),
                    "unit":'minutes'}
        
        consumption = {"total":self.get_total_consumption(),
                       "average":self.avg_consumption(),
                       "average per day":self.consumption_per_day(),
                       "largest":self.largest_mod().get_consumption(),
                       "unit":'Wh'}
        
        delta = {"average":self.avg_delta(),
                 "largest":self.largest_delta().delta(),
                 "unit":'W'}
        
        kpis = {"is modulating":self.is_modulating(),
                "duration":duration,
                "consumption":consumption,
                "delta":delta,
                "number of modulations":self.number_of_modulations(),
                "average number of modulations per day":self.modulations_per_day()}
        
        output_data = self.get_series()
        if output_data is not None:
            output_data = output_data.to_json()
        else:
            output_data = json.dumps(None)
        
        res = '{'
        res += '"analysis id":{id:s}'.format(id=json.dumps(self.analysis_id))
        res += ',"dates":{d:s}'.format(d=json.dumps(dates))
        res += ',"input data":{df:s}'.format(df=self.df.to_json())
        res += ',"output data":{df:s}'.format(df=output_data)
        res += ',"metadata":{m:s}'.format(m=json.dumps(metadata))
        res += ',"kpis":{k:s}'.format(k=json.dumps(kpis))
        res += '}'
        
        return res

class Modulation:
    """
        Modulation object, contains one single detected modulation behaviour
    """
    def __init__(self):
        """
            Init
        """
        self.series = None
    
    def __hash__(self):
        """
            Hash, to determine the uniqueness of a modulation

            Returns
            -------
            hash
        """
        return hash(str(self.series.name)+str(self.series.first_valid_index()))
    
    def __eq__(self, other):
        """
            Method to determine if one modulation is the same as another

            Parameters
            ----------
            other: Modulation

            Returns
            -------
            bool
        """
        try:
             ans = self.series.name == other.series.name and self.series.first_valid_index() == other.series.first_valid_index()
        except:
            return False
        else:
            return ans
        
    def set_series(self,series):
        """
            Sets input data of the modulation

            Parameters
            ----------
            series: Pandas Series
        """
        self.series = series
        
    def get_minutes(self):
        """
            Duration of the modulation in minutes

            Returns
            -------
            int
        """
        if self.series is None:
            return 0
        delta = self.series.index[-1] - self.series.index[0]
        seconds = delta.total_seconds()
        return int(seconds/60)
    
    def get_consumption(self):
        """
            Gas Consumption during the modulation

            Returns
            -------
            float
        """
        if self.series is None:
            return 0.
        _sum = self.series.sum()
        consumption = _sum/60
        return consumption
    
    def get_max(self):
        """
            Max value in series

            Returns
            -------
            float
        """
        try:
            return self.series.max()
        except:
            return 0.
    
    def get_min(self):
        """
            Min value in series

            Returns
            -------
            float
        """
        try:
            return self.series.min()
        except:
            return 0.
    
    def delta(self):
        """
            Difference between minimum and maximimum of the modulation

            Returns
            -------
            float
        """
        return self.get_max()-self.get_min()
    
    def drop_low_vals(self,tresh):
        """
            Drops values below a treshold from series

            Parameters
            ----------
            tresh: float or int
        """
        for ix,val in enumerate(self.series):
            if val < tresh:
                self.series[ix] = np.float('NaN')
        self.series = self.series.dropna()