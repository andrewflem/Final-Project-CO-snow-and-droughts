#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Thu Mar 23 14:55:38 2023

Script focusing on the correlation between snowfall and droughts 
in the western United States

@author = Andrew Fleming
@date = 2023-03-09
@license = MIT -- https://opensource.org/licenses/MIT
"""

import os
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import numpy as np

#%% Load snow data

#Specify folder name and variable names
subfolder1_name = 'Snow data'

#Create function
def readscan(filename):
    #read files
    data_snow = pd.read_csv(filename, header = 1, na_values = [-99.9], 
                   parse_dates=['Date'], index_col='Date')
    #Rename columns
    data_snow = data_snow.rename(columns={'WTEQ.I-1 (in) ': 'SWE_in','PREC.I-1 (in) ': 'Precip_in'})
       
    #Only have integrated data_snow so take difference for daily values
    data_snow['Precip_in']=data_snow['Precip_in'].diff()
    data_snow['SWE_in']=data_snow['SWE_in'].diff()
    
    #resample
    data_snow = data_snow.resample('D').mean(numeric_only=True)
   
    #Convert to cm 
    data_snow['Precip_cm'] = data_snow['Precip_in']*2.54
    data_snow['SWE_cm'] = data_snow['SWE_in']*2.54
   
    #replace negaive values with nan
    data_snow.loc[data_snow['Precip_cm']<0,'Precip_cm'] = np.nan
    data_snow.loc[data_snow['SWE_cm']<0,'SWE_cm'] = np.nan
    
    #Deleat unwanted columns
    data_snow = data_snow[['SWE_cm','Precip_cm']]
    return data_snow

filenames = os.listdir(subfolder1_name)
if 'data_snow' in globals():
    del data_snow
    
for filename in filenames:
    data_snow_small=readscan(subfolder1_name+ '\\' + filename)
    try:
        data_snow= pd.concat([data_snow,data_snow_small])
    except:
        data_snow= data_snow_small


# Make non-winter months NaN        
data_snow.loc[~((data_snow.index.month >= 12) | (data_snow.index.month <= 3))] = pd.NA
data_snow = data_snow.dropna()

data_snow = data_snow['1997-01-01':'2022-12-31']

#%% Load soil moisture data

#Specify folder name and variable names
subfolder2_name = 'Soil data'

#Create function
def readscan(filename):
    #read files
    data_sm = pd.read_csv(filename, header = 1, na_values = [-99.9], 
                   parse_dates=['Date'], index_col='Date')
    #Rename columns
    data_sm = data_sm.rename(columns={'SMS.I-1:-2 (pct)  (loam)': 'SM5',
                                'SMS.I-1:-4 (pct)  (loam)': 'SM10','SMS.I-1:-8 (pct)  (loam)': 'SM20',
                                'SMS.I-1:-20 (pct)  (loam)': 'SM50','SMS.I-1:-40 (pct)  (loam)': 'SM100'})
    
    #Replace negatives with nan
    data_sm.loc[data_sm['SM50']<0,'SM50'] = np.nan
    data_sm.loc[data_sm['SM100']<0,'SM100'] = np.nan
    
    #resample
    data_sm = data_sm.resample('D').mean(numeric_only=True)

    data_sm = data_sm[['SM5','SM10','SM20','SM50','SM100']]
    return data_sm

filenames = os.listdir(subfolder2_name)

for filename in filenames:
    data_sm_small=readscan(subfolder2_name+ '\\' + filename)
    try:
        data_sm= pd.concat([data_sm,data_sm_small])
    except:
        data_sm= data_sm_small

#Fill in Missing data
data_sm['SM5'] = data_sm['SM5'].fillna(data_sm['SM10'])
data_sm['SM10'] = data_sm['SM10'].fillna((data_sm['SM5'] +data_sm['SM20'])/2)
data_sm['SM20'] = data_sm['SM20'].fillna((data_sm['SM10'] +data_sm['SM50'])/2)
data_sm['SM50'] = data_sm['SM50'].fillna((data_sm['SM20'] +data_sm['SM100'])/2)
data_sm['SM100'] = data_sm['SM100'].fillna(data_sm['SM50'])

#Integrating  data       
data_sm['tot_soilmoisture'] = np.trapz(data_sm[['SM5', 'SM10', 'SM20', 'SM50', 'SM100']])

#Isolate SM to summer months
data_sm.loc[~((data_sm.index.month >= 6) | (data_sm.index.month <= 9))] = pd.NA
data_sm = data_sm.dropna()

#%% Creating annual data frame for SWE
    
#Counting Number of non-null values
nonnan_count = data_snow.notnull().groupby(data_snow.index.year).sum()

#Create new data frame
dfscan_fill1 = data_snow.interpolate()

#Calculate values
dfannual_SWE = dfscan_fill1[['SWE_cm']].groupby(data_snow.index.year).sum()

#%% Annual data frame for SM

#Counting Number of non-null values
nonnan_count = data_sm.notnull().groupby(data_sm.index.year).sum()

#Create new data frame
dfscan_fill2 = data_sm.interpolate()

#Calculate values
dfannual_SM = dfscan_fill2[['tot_soilmoisture']].groupby(data_sm.index.year).sum()

#%% Combine data frames

dfannual = dfannual_SWE['SWE_cm'],dfannual_SM['tot_soilmoisture']

#%%Create Time Series Plot for SWE

# Create plot 
fig1, ax = plt.subplots()

# Plot another data series
ax.plot(data_snow['Precip_cm'],  # x = 1st series, y = 2nd series)
        'b--',                            # Line Format
        label = 'Precipitation')         # series label for legend

# Plot one data series 
ax.plot(data_snow['SWE_cm'],  # x = 1st series, y = 2nd series)
        'k-',                           # Line Format
        label = 'SWE')       # series label for legend


# Add plot components 
ax.set_xlabel('Year')         # x-axis label 
ax.set_ylabel('cm')          # y-axis label
ax.set_title('Precipitation and SWE') # figure title
ax.legend()                                   # legend

# Optional command to make x-tick labels diagonal to avoid overlap
fig1.autofmt_xdate()  
    
#%%Create Time Series Plot for SM

# Create plot 
fig2, ax2 = plt.subplots()

# Plot another data series
ax2.plot(data_sm['SM5'],  # x = 1st series, y = 2nd series)
        'b',                            # Line Format
        label = '5cm')         # series label for legend

ax2.plot(data_sm['SM10'],  # x = 1st series, y = 2nd series)
        'r',                            # Line Format
        label = '10cm')         # series label for legend

ax2.plot(data_sm['SM20'],  # x = 1st series, y = 2nd series)
        'k',                            # Line Format
        label = '20cm')         # series label for legend

ax2.plot(data_sm['SM50'],  # x = 1st series, y = 2nd series)
        'g',                            # Line Format
        label = '50cm')         # series label for legend

ax2.plot(data_sm['SM100'],  # x = 1st series, y = 2nd series)
        'y',                            # Line Format
        label = '100cm')         # series label for legend


# Add plot components 
ax2.set_xlabel('Year')         # x-axis label 
ax2.set_ylabel('centimeters')          # y-axis label
ax2.set_title('Soil Moisture') # figure title
ax2.legend()                                   # legend

# Optional command to make x-tick labels diagonal to avoid overlap
fig2.autofmt_xdate() 

#%%Plot SM vs SWE

# Create plot 
fig3, ax3 = plt.subplots()

# Plot another data series
ax3.plot(dfannual_SM['tot_soilmoisture'], dfannual_SWE['SWE_cm'],  # x = 1st series, y = 2nd series)
        'bo',                            # Line Format
        label = '10cm')         # series label for legend

# Add plot components 
ax3.set_xlabel('SM')         # x-axis label 
ax3.set_ylabel('SWE')          # y-axis label
ax3.set_title('SM vs. SWE') # figure title
ax3.legend()                                   # legend

# Optional command to make x-tick labels diagonal to avoid overlap
fig3.autofmt_xdate() 

#%%Plotting

start_date = '1996-10-01'
end_date = '2022-09-30'

#Figure 1 time series
for i,v in enumerate(start_date):
    dataplot= data_sm[start_date:end_date] 
    fig, (ax1,ax2,ax3) = plt.subplots(3,
                                1, figsize=(10,16), sharex = True)

# Plot a Soil Moisture
    ax1.plot(dataplot['SM5'], 'ko', label= "5cm")  
    ax1.plot(dataplot['SM10'], 'ro', label= "10cm")  
    ax1.plot(dataplot['SM20'], 'bo', label= "20cm")  
    ax1.plot(dataplot['SM50'], 'yo', label= "50cm")  
    ax1.plot(dataplot['SM100'], 'go', label= "100cm")  
          
    ax1.legend(loc='center left',bbox_to_anchor= (1.0, 0.5))
    
# Add y-axis label    
    ax1.set_ylabel('Soil Moisture')   
    
# Add plot title
    ax1.set_title('Soil Moisture')
    
# Plot b Integrated SM
    ax2.plot(dataplot['tot_soilmoisture'], 'b-')
    ax2.set_ylabel('Integrated SM')

#Plot c Precip
    ax3.plot(data_snow['SWE_cm'], 'r-')
    ax3.set_ylabel('SWE (cm)')
    

#%% Linear Regression  
#dfannual = dfannual.dropna()

#Create function
def regressplot(time_series,data_series, y_label, figtitle):

    #Calculate parametric linear regression values
    lsq_coeff = stats.linregress(time_series,data_series)
    
    #Calculate non-parametric regression values
    sen_coeff = stats.theilslopes(data_series,time_series, 0.95)
    
    #Calculate non-parametric correlation
    tau = stats.kendalltau(time_series,data_series)

    #Create plot and show time eries of input data series
    fig, ax = plt.subplots()
    ax.plot(data_series, 'k.')
    #Parametric best fit line
    ax.plot(time_series, lsq_coeff.intercept + lsq_coeff.slope *
           time_series, 'b-', label='Linear regression')
    #Annotation Placement
    xx = ax.get_xlim()
    yy = ax.get_ylim()

    #Display least squares sparametric slope and correlation on graph
    ax.annotate(f'Least-squares slope = {lsq_coeff.slope:.4f} +/- {2*lsq_coeff.stderr:.4f}',
                xy=(xx[1]-0.05*(xx[1]-xx[0]), yy[0] + 0.18*(yy[1]-yy[0])),
                horizontalalignment='right')
    ax.annotate(f'Least-squares correlation = {lsq_coeff.rvalue:.4f}; p = {lsq_coeff.pvalue:.4f}',
                xy=(xx[1]-0.05*(xx[1]-xx[0]), yy[0] + 0.13*(yy[1]-yy[0])),
                horizontalalignment='right')

    #Non-parametric best fit line
    ax.plot(time_series, sen_coeff.intercept + sen_coeff.slope *
               time_series, 'y-', label='Theil-Sen regression')

    #Display non-parametric slope and correlation on graph
    ax.annotate(f'Theil-Sen slope = {sen_coeff.slope:.4f} +/- {0.5*(sen_coeff.high_slope - sen_coeff.low_slope):.4f}',
                    xy=(xx[1]-0.05*(xx[1]-xx[0]), yy[0] + 0.08*(yy[1]-yy[0])),
                    horizontalalignment='right')
    ax.annotate(f'Tau correlation = {tau.correlation:.4f}; p = {tau.pvalue:.4f}',
                    xy=(xx[1]-0.05*(xx[1]-xx[0]), yy[0] + 0.03*(yy[1]-yy[0])),
                    horizontalalignment='right')

    ax.set_title(figtitle)
    ax.set_ylabel(y_label)
    ax.legend(loc='upper center')
    plt.show()
