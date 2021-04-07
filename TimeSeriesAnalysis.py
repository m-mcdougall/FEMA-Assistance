# -*- coding: utf-8 -*-

#To be run after Date_Processing.py

import pandas as pd
import os
import numpy as np


#Set working directory
wd=os.path.abspath('C://Users//Mariko//Documents//GitHub//FEMA-Assistance//Data//')
os.chdir(wd)

pd.set_option('display.max_columns', None)

#%%


## Start with loading the Disaster Declaration Summaries
disasters = pd.read_csv(wd+'//DailyDisasters.csv', parse_dates=['declarationDate','incidentBeginDate', 
                                                          'incidentEndDate', 'disasterCloseoutDate', 'Date'])

disasters.Date = disasters.Date.dt.date
#%%

#OHE

disasters2 = disasters.copy()


y=disasters2.groupby('Date').agg({'county': 'unique','state_y': 'unique', 'declarationType':'unique',
                    'incidentType':'unique','declarationTitle':'unique','ihProgramDeclared':'sum',
                    'iaProgramDeclared':'sum','paProgramDeclared':'sum','hmProgramDeclared':'sum',
                    'PublicProjectNumber':'sum', 'PublicApproved':'sum','PrivateDamage':'sum',
                    'PrivateApproved':'sum','PrivateNumberApproved':'sum',})

#%%

x=y.copy()

#Get a count for number of unique counties and states
x['UniqueCounty'] = y.county.str.len()
x['UniqueState'] = y.state_y.str.len()

#Number of distinct events
x['UniqueDisasters'] = y.declarationTitle.str.len()


#OHE
x['declarationDR'] = y.declarationType.apply(lambda x: 'DR' in x)
x['declarationEM'] = y.declarationType.apply(lambda x: 'EM' in x)

# Disaster type OHE
for i in disasters2.incidentType.unique():
    x[i] = y.incidentType.apply(lambda x: i in x)
    

x=x.drop(['county', 'state_y', 'declarationType'], axis=1)

#%%


#Create a column, with one date for each day between start and end of the emergency
days = pd.DataFrame(pd.date_range(x.index.min(), x.index.max(), freq='d', ))


#Base
base = x.head(1).copy()

base['incidentType'] = ['None',]
base['declarationTitle'] = ['None',]

for col in ['ihProgramDeclared','iaProgramDeclared', 'paProgramDeclared', 'hmProgramDeclared',
           'PublicProjectNumber', 'PublicApproved', 'PrivateDamage',
           'PrivateApproved', 'PrivateNumberApproved', 'UniqueCounty',
           'UniqueState', 'UniqueDisasters']:

    base[col] = 0

for col in ['declarationDR', 'declarationEM',
           'Severe Storm(s)', 'Flood', 'Severe Ice Storm', 'Tornado', 'Hurricane',
           'Fire', 'Earthquake', 'Terrorist', 'Coastal Storm', 'Snow', 'Typhoon',
           'Freezing', 'Dam/Levee Break', 'Tsunami', 'Other', 'Chemical']:

    base[col] = False


days.index = days[0].dt.date

for col in base:
    days[col] = base[col][0]

days=days.drop([0], axis=1)



for i in x.index:
    days.loc[i]=x.loc[i]


days['TotalApproved'] = days['PublicProjectNumber'] + days['PrivateNumberApproved']
days['TotalCost'] = days['PublicApproved'] + days['PrivateApproved']

#%%
import matplotlib.pyplot as plt
    
plt.plot(days.TotalApproved)
plt.show()

plt.plot(days.TotalCost)
plt.show()


plt.plot(days[days.Terrorist==False].TotalCost)
plt.show()


plt.plot(days[days.Terrorist==False].UniqueDisasters)
plt.show()










