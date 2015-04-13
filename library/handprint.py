import copy
import json
import matplotlib.pyplot as plt
import pandas as pd
from analysis import Analysis
from regression import Linregress, Segmented_Linregress

class Handprint(Analysis):
    """
        Energetic Handprint Analysis.

        Takes daily gas and degree day data en performs a regression analysis.
    """
    
    def __init__(self,gas,hdd,analysis_id=None,elec=None,water=None):
        """
            Init Analysis

            Parameters
            ----------
            gas: Pandas DataSeries, daily gas use in Wh
            hdd: Pandas DataSeries, daily degree days, in Kelvin
            analysis_id: string, optional
            elec: Pandas DataSeries, optional, daily electricity use in Wh
                optional, used to refine the analysis when supplied
            water: Pandas DataSeries, optional, daily water user in L
                optional, used to refine the analysis when supplied
        """
        super(Handprint, self).__init__(analysis_id)
        
        #make copy's of all timeseries
        temp_gas = copy.deepcopy(gas)
        temp_hdd = copy.deepcopy(hdd)
        temp_elec = copy.deepcopy(elec)
        temp_water = copy.deepcopy(water)
        
        #rename column names
        temp_gas.name = 'gas'
        temp_hdd.name = 'hdd'
        if temp_elec is not None:
            temp_elec.name = 'elec'
        if temp_water is not None:
            temp_water.name = 'water'
            
        #set flags
        self.has_elec = temp_elec is not None
        self.has_water = temp_water is not None
        
        #concatenate timeseries into one dataframe
        self.df = pd.concat([temp_gas,temp_hdd,temp_elec,temp_water],axis=1)
        
        #calculate all trends, after that get_best_trend() will return the one with the highest score
        self.trends = self.calculate_trends()
    
    def calculate_trends(self):
        """
            Calculate a lot of different trends according to multiple methods,
            store them so the best trend can be chosen later.

            Returns
            -------
            array of Trend objects
        """
        temp = []
        
        #temp.append(self.get_linregress())
        #temp.append(self.get_linregress_week())
        temp.append(self.get_segmented())
        temp.append(self.get_segmented_week())
        temp.append(self.get_businessday())
        temp.append(self.get_weekend())
        
        
        weekdays = ['W-MON','W-TUE','W-WED','W-THU','W-FRI','W-SAT','W-SUN']
        for weekday in weekdays:
            temp.append(self.get_weekday(weekday))
        
        return [trend for trend in temp if trend is not None]
    
    def get_linregress(self):
        """
            Calculate linear regression on daily basis

            Returns
            -------
            Trend
        """
        if not hasattr(self,'linregress'):
            df_temp = copy.deepcopy(self.df)
                        
            df_temp = self.filter_presence(df_temp)
                
            if df_temp['gas'].dropna().empty:
                return None

            self.linregress = Linregress(x = df_temp['hdd'].tolist(),
                                         y = df_temp['gas'].tolist(),
                                         label = 'Linear Regression')
        return self.linregress
    
    def get_linregress_week(self):
        """
            Calculate linear regression on weekly basis,
            returned values as average per day

            Returns
            -------
            Trend
        """

        if not hasattr(self,'linregress_week'):
            
            df_temp = copy.deepcopy(self.df)
            df_temp = self.average_week(df_temp_day)
                        
            df_temp = self.filter_presence_week(df_temp_day=df_temp_day,
                                                df_temp=df_temp)
            
            if df_temp['gas'].dropna().empty:
                return None
                
            else:
                self.linregress_week = Linregress(x = df_temp['hdd'].tolist(),
                                                      y = df_temp['gas'].tolist(),
                                                      label = 'Linear Regression, Weekly mean'
                                                      )
        return self.linregress_week
    
    def get_segmented_week(self):
        """
            Calculate segmented regression on weekly basis,
            returned values as average per day

            Returns
            -------
            Trend
        """
        if not hasattr(self,'segmented_week'):
            
            df_temp_day = copy.deepcopy(self.df)
            
            df_temp = self.average_week(df_temp_day)
                        
            df_temp = self.filter_presence_week(df_temp_day=df_temp_day,
                                                df_temp=df_temp)
            
            if df_temp['gas'].dropna().empty:
                return None
                
            else:
                self.segmented_week = Segmented_Linregress(x = df_temp['hdd'].tolist(),
                                                        y = df_temp['gas'].tolist(),
                                                        label = 'Segmented Regression, Weekly mean'
                                                        )
        return self.segmented_week
    
    def get_businessday(self):
        """
            Calculate segmented regression on businessday basis,
            returned values as average per day

            Returns
            -------
            Trend
        """

        if not hasattr(self,'businessday'):
            
            df_temp_day = copy.deepcopy(self.df)
            df_temp_day = df_temp_day.resample('B')
            
            df_temp = self.average_week(df_temp_day)
                        
            df_temp = self.filter_presence_week(df_temp_day=df_temp_day,
                                                df_temp=df_temp)
            
            if df_temp['gas'].dropna().empty:
                return None
                
            else:
                self.businessday = Segmented_Linregress(x = df_temp['hdd'].tolist(),
                                                        y = df_temp['gas'].tolist(),
                                                        label = 'Segmented Regression, Businessday mean'
                                                        )
        return self.businessday
    
    def get_weekday(self,day):
        """
            Calculate segmented regression for a certain day in the week

            Parameters
            ----------
            day: string ['W-MON','W-TUE','W-WED','W-THU','W-FRI','W-SAT','W-SUN']

            Returns
            -------
            Trend
        """
            
        df_temp = copy.deepcopy(self.df)
        df_temp = df_temp.resample(day,how='last')
        df_temp = self.filter_presence(df_temp)
            
        if df_temp['gas'].dropna().empty:
            return None
                
        else:
            return Segmented_Linregress(x = df_temp['hdd'].tolist(),
                                        y = df_temp['gas'].tolist(),
                                        label = 'Segmented Regression, '+day
                                        )
    
    def get_weekend(self):
        """
            Calculate segmented regression for days in the weekend (saturday and sunday)

            Returns
            -------
            Trend
        """
        if not hasattr(self,'weekend'):
            
            df_temp_day = copy.deepcopy(self.df)
            df_temp_day = df_temp_day.resample('W-SAT',how='last').add(df_temp_day.resample('W-SUN',how='last'),fill_value=0)
            
            df_temp = copy.deepcopy(self.average_week(df_temp_day))
                        
            df_temp = self.filter_presence_week(df_temp_day=df_temp_day,
                                                df_temp=df_temp)
            
            if df_temp['gas'].dropna().empty:
                return None
                
            else:
                self.weekend = Segmented_Linregress(x = df_temp['hdd'].tolist(),
                                                    y = df_temp['gas'].tolist(),
                                                    label = 'Segmented Regression, weekend mean'
                                                    )
        return self.weekend
    
    def get_segmented(self):
        """
            Calculate a segmented regression on daily basis

            Returns
            -------
            Trend
        """
        if not hasattr(self,'segmented'):
            df_temp = copy.deepcopy(self.df)
            
            df_temp = self.filter_presence(df_temp)
                
            if df_temp['gas'].dropna().empty:
                return None
            
            self.segmented = Segmented_Linregress(x = df_temp['hdd'].tolist(),
                                                     y = df_temp['gas'].tolist(),
                                                     label = 'Segmented Regression, daily basis'
                                                     )
        return self.segmented
    
    def filter_presence(self,df_temp):
        """
            Use electricity and water data to determine if somebody was home or not,
            filter out the days when nobody was home.

            Parameters
            ----------
            df_temp: Pandas DataFrame

            Returns
            -------
            Pandas DataFrame
        """
        before = df_temp.index.size
        
        #if the analysis has electricity data, use it to filter absences
        if self.has_elec:
            presence = get_presence(gas = df_temp['gas'],
                                    other = df_temp['elec'])
            df_temp = df_temp[presence > 0]
                
        #if the analysis has water data, use it to filter absences
        if self.has_water:
            presence = get_presence(gas = df_temp['gas'],
                                        other = df_temp['water'])
            df_temp = df_temp[presence > 0]
            
        #save the number of filtered days
        if not hasattr(self,'absent_days'):
            self.absent_days = before - df_temp.index.size
                
        return df_temp
    
    def filter_presence_week(self,df_temp_day,df_temp):
        """
            Use electricity and water data to determine if somebody was home or not
            filter out the weeks where there were non-active days

            Parameters
            ----------
            df_temp_day: Pandas DataFrame with daily data
            df_temp: Pandas DataFrame with weekly data

            Returns
            -------
            Pandas DataFrame
        """
        before = df_temp.index.size
        
        #if the analysis has electricity data, use it to filter absences
        if self.has_elec:
            presence = get_presence(gas = df_temp_day['gas'],
                                    other = df_temp_day['elec']
                                    ).resample('W-MON',how='min',closed='left',label='left')
            df_temp = df_temp[presence > 0]

        #if the analysis has water data, use it to filter absences   
        if self.has_water:
            presence = get_presence(gas = df_temp_day['gas'],
                                    other = df_temp_day['water']
                                    ).resample('W-MON',how='min',closed='left',label='left')
            df_temp = df_temp[presence > 0]
            
        #save number of filtered weeks
        if not hasattr(self,'absent_weeks'):
            self.absent_weeks = before - df_temp.index.size
            
        return df_temp
    
    def average_week(self,df_temp):
        """
            Resample data to a weekly interval,
            average the values
            set the date to the monday at the begin of the interval
            drop the heading and trailing week if they have less than 7 days

            Parameters
            ----------
            df_temp: Pandas DataFrame

            Returns
            -------
            Pandas DataFrame
        """
        begin = df_temp.index[0]
        end = df_temp.index[-1]
        df_temp = df_temp.resample('W-MON',how='mean',closed='left',label='left') 
        if (end - df_temp.index[-1]).days < 7:
            end = df_temp.index[-2]
        
        if not hasattr(self,'incomplete_weeks'):
            self.incomplete_weeks = df_temp.index.size - df_temp[begin:end].index.size
        
        return df_temp[begin:end]
    
    def get_best_trend(self):
        """
            Returns the best trend from self.trends

            Returns
            -------
            Trend
        """
        best = None
        for trend in self.trends:
            if best is None or trend > best:
                best = trend
                
        return best
    
    def to_json(self):
        """
            Grabs the json results from the best trend, adds some more metadata and returns
            a json string with all results

            Returns
            -------
            JSON formatted string
        """
        trend = self.get_best_trend()
    
        metadata = {"has electricity sensor":self.has_elec,
              "has water sensor":self.has_water,
              "incomplete weeks":self.incomplete_weeks,
              "absent days":self.absent_days,
              "absent weeks":self.absent_weeks}
    
        dates = {"start":str(self.df.index[0].date()),"end":str(self.df.index[-1].date())}
    
        res = '{'
        res += '"analysis id":{id:s}'.format(id=json.dumps(self.analysis_id))
        res += ',"dates":{d:s}'.format(d=json.dumps(dates))
        res += ',"input data":{df:s}'.format(df=self.df.to_json())
        res += ','+trend.to_json()
        res += ',"metadata":{m:s}'.format(m=json.dumps(metadata))
        res += '}'
        
        return res
    
    def to_plt(self):
        """
            Grabs the best trend and creates a scatterplot

            Returns
            -------
            matplotlib figure object
        """
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
    
        ax1.scatter(self.df['hdd'], self.df['gas'], alpha=.1, s=10)

        trend = self.get_best_trend()
        if trend is None:
            return None
        
        temp = sorted(zip(trend.x,trend.y))
        
        x = [X for (X,Y) in temp]
        y = [Y for (X,Y) in temp]
        
        ax1.scatter(x, y, alpha=.4, s=20)
    
        if trend.bp is None:
            function = "{s:.0f}x + {i:.0f}".format(s = trend.slope, i = trend.intercept)
        else:
            function = "{s0:.0f}x + {i0:.0f} for x <= {bp:.1f}\n{s1:.0f}x + {i1:.0f} for x > {bp:.1f}".format(s0=trend.slope[0],
                                                                                                          s1=trend.slope[1],
                                                                                                          i0=trend.intercept[0],
                                                                                                          i1=trend.intercept[1],
                                                                                                          bp=trend.bp)
                                                                                                             
        label = "{l:s}\n{start:s} - {end:s}\nReliability Factor: {r:.2f}\nR2: {r2:.2f} \nCV(RMSE): {cvrmse:.2f}\nFunction: {f:s}".format(l = trend.label,
                                                                                                                                     start = str(self.df.index[0].date()),
                                                                                                                                     end = str(self.df.index[-1].date()),
                                                                                                                                     r = trend.get_reliability(),
                                                                                                                                     r2 = trend.r2,
                                                                                                                                     cvrmse = trend.cvrmse,
                                                                                                                                     f = function)
        
        x = [X for X in self.df['hdd']]
        x = sorted(x)
        
        ax1.plot(x, trend.p(x), '-', label=label)
        
        fig.suptitle(self.analysis_id)
        plt.xlabel('Degree Days')
        plt.ylabel('Gas Consumption [Wh]')
        plt.legend()
        plt.legend(loc='upper left')
    
        x1,x2,y1,y2 = plt.axis()
        x1 = min(0,x1)
        x2 = max(20,x2)
        plt.axis((x1,x2,0,y2))
        
        return fig

def get_presence(gas,other):
    """
        Uses an other datastream (water or electricity) to determine if somebody was home or not
        Gas use gets compared to the 30-day average. If it drops under a certain treshold,
        and the other datastream also drops under a certain treshold, it might indicate that
        nobody was home that day.

        Parameters
        ----------
        gas: Pandas DataSeries
        other: Pandas DataSeries

        Returns
        -------
        Pandas DataSeries
    """

    '''
        Set the sensitivity of the algorithm
    '''
    factor_gas = .75 #nobody was home if gas use drops under 75% of the average
    factor_other = .6 #AND the other datastream drops under 60% of the average
    
    #make copies of the data so no original dataframes get changed
    ts_gas = copy.deepcopy(gas)
    ts_other = copy.deepcopy(other)
    
    #subtract the baseline of the data
    ts_gas = ts_gas - ts_gas.min()
    ts_other = ts_other - ts_other.min()
    
    #take the 30-day average
    average_gas = pd.rolling_mean(ts_gas,30,center=True).fillna(method='bfill').fillna(method='pad')
    average_other = pd.rolling_mean(ts_other,30,center=True).fillna(method='bfill').fillna(method='pad')
    
    #multiply the average with the tresholds so we get the decision line 
    average_gas *= factor_gas
    average_other *= factor_other
    
    presence = []
    #loop all values toghether with the treshold value
    for val_g, val_o, avg_g, avg_o in zip(ts_gas, ts_other, average_gas, average_other):
        if val_g < avg_g and val_o < avg_o:
            #if both values are under the treshold: nobody was home, append 0
            presence.append(0)
        else:
            presence.append(1)
            
    #return a series with the same index as the original
    temp = pd.Series(index = ts_gas.index,
                     data = presence)
    return temp