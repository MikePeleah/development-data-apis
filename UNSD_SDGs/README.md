# United Nations Statistics Division SDG API

## API Documentation 
In [UNSD SDG API](https://unstats.un.org/SDGAPI/swagger/) you will be able to explore the official SDG data reported by the custodian agencies. 

## Particularities
**UNSD uses [M49 country codes](https://unstats.un.org/unsd/methodology/m49/)**
**Every series has 'dimensions'**, i.e. breakdownd by locality, gender, etc. 

## Code Examples
**Get Global SDG Data.py** Get global indicators for selected list of countries and selected SDGs. ```dim_ignore``` is a list of dimensions to be ignored. Currently it includes only 'Reporting Type', as database include only data from custodian agencies. ```dim_aggrs``` provides a list of meaningful dimensions for each series. Note that this list could change for different releases. Note that available dimension code could vary for countries, especailly for education indicators. 
