# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from sklearn.linear_model import LinearRegression


#Set working directory
wd=os.path.abspath('C://Users//Mariko//Documents//GitHub//FEMA-Assistance//Data//')
raw_wd=wd+'//Raw//'
os.chdir(raw_wd)

pd.set_option('display.max_columns', None)
#%%


## Start with loading the Disaster Declaration Summaries

disasters = pd.read_csv('DisasterDeclarationsSummaries.csv', parse_dates=[4,5,12,13,14])


#Select columns to keep


#These variables are specific to the record, not the event
disasters = disasters.drop(['hash','lastRefresh', 'id' ], axis=1)

#This is already represented in the declaration date, but has less information
disasters = disasters.drop(['fyDeclared'], axis=1)

#This is an internal code, not needed
disasters = disasters.drop(['placeCode'], axis=1)

disasters.disasterNumber.unique().shape[0] == disasters.shape[0]

#%%

#Now check the Public programs
public = pd.read_csv('PublicAssistanceFundedProjectsSummaries.csv', parse_dates=[1])



#Select columns to keep

#These variables are specific to the record, not the event
public = public.drop(['hash','lastRefresh', 'id' ], axis=1)


#%%

#Now check the Home Owners programs
private_own = pd.read_csv('HousingAssistanceOwners.csv', low_memory=False)


#Select columns to keep

#These variables are specific to the record, not the event
private_own = private_own.drop(['id' ], axis=1)

#This is likely too specific. We'll keept the total number of inspected, but leave out how much each cost
private_own = private_own.drop(['noFemaInspectedDamage', 'femaInspectedDamageBetween1And10000', 'femaInspectedDamageBetween10001And20000',
                      'femaInspectedDamageBetween20001And30000', 'femaInspectedDamageGreaterThan30000', 
                      'approvedBetween1And10000', 'approvedBetween10001And25000', 'approvedBetween25001AndMax', 'totalMaxGrants'], axis=1)


#Now check the Rental programs
private_rent = pd.read_csv('HousingAssistanceRenters.csv', low_memory=False)

private_rent = private_rent.drop(['id' ], axis=1)

#This is likely too specific. We'll keept the total number of inspected, but leave out how much each cost
private_rent = private_rent.drop(['approvedBetween1And10000', 'approvedBetween10001And25000', 'approvedBetween25001AndMax',
                        'totalMaxGrants','totalInspectedWithNoDamage',
                        'totalWithModerateDamage', 'totalWithMajorDamage',
                        'totalWithSubstantialDamage', ], axis=1)



#Combine the rental and homeowner data


#Filter for only columns we intend to use
private_own_filter=private_own.filter(['disasterNumber', 'totalDamage', 'totalApprovedIhpAmount', 'approvedForFemaAssistance', 'rentalAmount', 'zipCode'])
private_rent_filter=private_rent.filter(['disasterNumber', 'totalApprovedIhpAmount', 'approvedForFemaAssistance', 'zipCode'])

#Groupby the diaster, and get the total amount for each value (originally seperated by zip code)
#Remove the rental amount - this is for private homeowners, by the looks
private_own_filter=private_own_filter.groupby(['disasterNumber', 'zipCode']).sum().reset_index()
private_own_filter['totalApprovedIhpAmount'] = private_own_filter['totalApprovedIhpAmount'] - private_own_filter['rentalAmount']
private_own_filter.drop(['rentalAmount'], axis=1, inplace=True)


#Groupby the diaster, and get the total amount for each value (originally seperated by zip code)
private_rent_filter=private_rent_filter.groupby(['disasterNumber', 'zipCode']).sum().reset_index()

columns_dict={col:col+'_rental' for col in private_rent_filter.columns if col not in ['disasterNumber', 'zipCode']}
private_rent_filter=private_rent_filter.rename(columns=columns_dict)


#Merge the Owner and rental dataframes together
private=private_own_filter.merge(private_rent_filter, on=['disasterNumber', 'zipCode'], how='left')
private=private.fillna(0) #Fill gaps that arise (Disaster zip codes that did not have rental claims)


#Add together the relevant columns, then drop the extras

for col in columns_dict:
    print(f'\n {col}')
    print(f'{private[col].iloc[15]} + {private[columns_dict[col]].iloc[15]}')
    private[col] = private[col] +private[columns_dict[col]]
    print(f'{private[col].iloc[15]}')

    private=private.drop(columns_dict[col], axis=1)


del private_own_filter,private_rent_filter, private_own, private_rent, columns_dict, col
#%%

zips = pd.read_csv(wd+'\\ZIP-COUNTY-FIPS_2018-03.csv')

#Seperate the Fips Codes int state and county
zips['fipsStateCode'] = zips['STCOUNTYFP'].astype('str').str[:-3]
zips['fipsStateCode'] = zips['fipsStateCode'] .astype(int)

zips['fipsCountyCode'] = zips['STCOUNTYFP'].astype('str').str[-3:]
zips['fipsCountyCode'] = zips['fipsCountyCode'] .astype(int)

#Seperate out the county name
zips['county'] = zips['COUNTYNAME'].str.replace('County','')


#Merge into the Private data
zips_private = zips.filter(['fipsStateCode', 'fipsCountyCode', 'ZIP'])
zips_private=zips_private.rename(columns={'ZIP':'zipCode'})
zips_private['zipCode']=zips_private['zipCode'].astype(str)

private=private.merge(zips_private, on=['zipCode'], how='left')


#%%
#Merge into Public Data



#%%

#Check how many are in all sets

ids_dis=disasters.disasterNumber.unique()
ids_pub=public.disasterNumber.unique()
ids_pvt=private.disasterNumber.unique()

