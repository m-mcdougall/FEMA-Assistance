# -*- coding: utf-8 -*-

#To be run after Data_Processing.py

import pandas as pd
import os
import numpy as np


#Set working directory
wd=os.path.abspath('C://Users//Mariko//Documents//GitHub//FEMA-Assistance//Data//')
os.chdir(wd)

pd.set_option('display.max_columns', None)

#%%


## Start with loading the Disaster Declaration Summaries
disasters = pd.read_csv('DataDisasters.csv', parse_dates=['declarationDate','incidentBeginDate', 
                                                          'incidentEndDate', 'disasterCloseoutDate'])



#%%

def daily_disasters(i, disasters):
    """
    Create a daily representation for each disaster declaration.
    
    i: The row iterator from the database
    disasters: The disasters database loaded from 'DataDisasters.csv'
    """
        
    #Load the row from the main database
    row=disasters.iloc[i,:]
    
    #Create a column, with one date for each day between start and end of the emergency
    days = pd.DataFrame(pd.date_range(row.incidentBeginDate, (row.incidentEndDate)+pd.Timedelta(1, unit='d'), freq='d', ))
    
    #Duplicate the row for each day it occured, and add the date column
    events=[]
    events.extend([list(row)]*days.shape[0])
    events=pd.DataFrame(events, columns=row.index)
    events['Date'] = days
    
    
    #Divide the expenses and approvals evenly between all days it occured
    for col in ['PublicProjectNumber', 'PublicApproved', 'PrivateDamage', 'PrivateApproved', 'PrivateNumberApproved']:
        events[col] = events[col]/days.shape[0]

    return events

#%%
    
all_disasters_days=[]

for i in range(disasters.shape[0]):
    all_disasters_days.append(daily_disasters(i, disasters))


x=pd.concat(all_disasters_days)
    
#Save the dataset to file
x.to_csv(wd+'//DailyDisasters.csv', index=False) 
#%%


    
    
    
    
    
    
    
    
    
    
    
    
    