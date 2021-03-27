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


#%%

#Now check the Public programs
public = pd.read_csv('PublicAssistanceFundedProjectsSummaries.csv', parse_dates=[1])



#Select columns to keep

#These variables are specific to the record, not the event
public = public.drop(['hash','lastRefresh', 'id' ], axis=1)


#FEMA did not used to look at counties within PR, so add a special category so they get covered too
old_pr=public.loc[public['state']=='Puerto Rico', 'county'].isna()
old_pr=old_pr[old_pr==True].index.values

for i in old_pr:
    public.loc[i, 'county'] = 'Statewide'

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

#Load the zip code - Fips file
zips = pd.read_csv(wd+'\\ZIP-COUNTY-FIPS_2018-03.csv')

#Get a list of us state abbreviations
runfile(os.path.abspath('../../')+'//UsStateAbbreviations.py')


#Seperate the Fips Codes int state and county
zips['fipsStateCode'] = zips['STCOUNTYFP'].astype('str').str[:-3]
zips['fipsStateCode'] = zips['fipsStateCode'] .astype(int)

zips['fipsCountyCode'] = zips['STCOUNTYFP'].astype('str').str[-3:]
zips['fipsCountyCode'] = zips['fipsCountyCode'] .astype(int)

#Seperate out the county name
zips['county'] = zips['COUNTYNAME'].str.replace(' County','')
zips['county'] = zips['county'].str.replace(' Municipio','')

#Make a full text version of the state name
zips['state'] = zips['STATE'].replace(abbrev_us_state)
zips=zips.drop(['STATE'], axis=1)




#Merge into the Private data
zips_private = zips.filter(['fipsStateCode', 'fipsCountyCode', 'ZIP'])
zips_private=zips_private.rename(columns={'ZIP':'zipCode'})
zips_private['zipCode']=zips_private['zipCode'].astype(str)

private=private.merge(zips_private, on=['zipCode'], how='left')




#Merge into Public Data
zips_public = zips.filter(['fipsStateCode', 'fipsCountyCode', 'county', 'state'])
zips_public=zips_public.drop_duplicates()


#Add a "statewide" option
for state in zips_public['state'].unique():
    sample=zips_public[zips_public.state == state].iloc[0,:]
    zips_public = zips_public.append({'fipsStateCode':sample.fipsStateCode, 'fipsCountyCode':999, 'county':'Statewide', 'state':state}, ignore_index=True)

#Alaska needs additional filtering
public['county'] = public['county'].str.replace(' \(CA\)','')


public=public.merge(zips_public, on=['county', 'state'], how='left')






#%%

#Group and aggregate the data to have one request summary pre disaster
#Originally organized by individual releif request.


private_group=private.drop(['zipCode'], axis=1)
private_group=private_group.groupby(['disasterNumber','fipsStateCode', 'fipsCountyCode']).sum().reset_index()

public_group=public.groupby(['disasterNumber','state', 'county']).agg({'numberOfProjects': np.sum,'federalObligatedAmount': np.sum,
              'fipsStateCode':'first', 'fipsCountyCode':'first'}).reset_index()

#%%

#Merge private and public


private_group.rename({'totalDamage': 'PrivateDamage', 'totalApprovedIhpAmount':"PrivateApproved",
                'approvedForFemaAssistance':"PrivateNumberApproved"}, axis=1, inplace=True)



public_group.rename({'numberOfProjects': 'PublicProjectNumber', 'federalObligatedAmount':"PublicApproved"},
                    axis=1, inplace=True)


aidRequests=public_group.merge(private_group, on=['disasterNumber','fipsStateCode', 'fipsCountyCode'], how='outer')

#%%
#These are the private requests for aid in counties that did not request FEMA aid, or received it through state-wide funds
fill_in = aidRequests[aidRequests.state.isna()].copy()


#Create and ID of the fips state and county codes
fill_in['ID']=fill_in.fipsStateCode.astype(int).astype(str)+'-'+fill_in.fipsCountyCode.astype(int).astype(str)
fill_in=fill_in.reset_index()
fill_in.index=fill_in.ID

#Create and ID of the fips state and county codes
zips_ids = zips.copy()
zips_ids['ID']=zips_ids.fipsStateCode.astype(int).astype(str)+'-'+zips_ids.fipsCountyCode.astype(int).astype(str)
zips_ids.index=zips_ids.ID
zips_ids=zips_ids.filter([ 'county', 'state'], axis=1).drop_duplicates()


#Merge the state and county information based on the IDs created above
fill_in.county = zips_ids.county
fill_in.state = zips_ids.state

#Reset to the original index, drop unneeded columns
fill_in.index=fill_in['index']
fill_in=fill_in.drop(['index', 'ID'], axis=1)

#%%

#Return the filled-in values to the aid requests
aidRequests.loc[fill_in.index, :] = fill_in

#Fill the nan values (which are now exclusively numeric)
aidRequests=aidRequests.fillna(0)


#%%

#Check how many are in all sets

#ids_dis=disasters.disasterNumber.unique()
#ids_pub=public.disasterNumber.unique()
#ids_pvt=private.disasterNumber.unique()

