#################################################################################################################
##
## Script for getting global SDG data through United Nations Statistics Division SDG API.
## API Documentation https://unstats.un.org/SDGAPI/swagger/
## GitHub https://github.com/MikePeleah/development-data-apis
## For comments and suggestions Mike.Peleah@gmail.com
##
#################################################################################################################

import json
import requests
import os
import re
import csv
from random import randint
from time import sleep

def progress_bar(done, total, l=10):
    pdone = done / total
    a = int(pdone * l)
    b = l - a 
    return "%d done out of %d, %4.1f%% done [%s%s]" % (done, total, pdone*100, u'\u2588'*a, u'\u2591'*b)

def try_get(url, ntries=3, delay=10, verbose = False):
    """
    Try to get url for ntries, after each unsuccessful attempt delay for delay seconds
    return {'code': result code, "Ok" if Ok, "Error" else
            'result': result of get}
    """
    attempts = ntries

    while attempts>0:
        attempts_try = attempts
        if verbose:
            print("%d attemps left, trying %s" % (attempts, url))
        try:
            result = requests.get(url)
            code = "Ok"
            attempts = 0
            result.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            attempts = 0
            code = "Error"
            result = "Http Error: %s" % errh
            if verbose:
                  print (result)
        except requests.exceptions.ConnectionError as errc:
            attempts = attempts_try - 1
            code = "Error"
            result = "Error Connecting: %s" % errc
            if verbose:
                  print (result)
            sleep(delay)
        except requests.exceptions.Timeout as errt:
            attempts = attempts_try - 1
            code = "Error"
            result = "Timeout Error: %s" % errt
            if verbose:
                  print (result)
            sleep(delay)
        except requests.exceptions.RequestException as err:
            attempts = 0
            code = "Error"
            if verbose:
                  print (result)
            result = "Oops: Something Else %s" % err
        if verbose:
            print("  ",code, result if code=="Error" else "")
    return {'code': code, 'result': result}

def get_UNSTAT_meta(series, verbose):
    """
    Get metadata for series from UNSTAT database
    input is list of series
    return list of dictionaries
        "code": series code,
        "name": series name,
        "source": description of data source,
        "metadata": link to metadata 
    list includes all possible disaggregations
    """
    UNSTAT_meta = []
    n_series = len(series)
    for i, that_series in enumerate(series):
        d = that_series['description']
        s = that_series['code']
        indicator = that_series['indicator'][0]    # 'indicator' is a list 
        if verbose:
            print("Handling ", s)
        # check if series has some diaggregations
        if s in dim_aggrs.keys():
            # then get dimesions 
            dims_req = requests.get("https://unstats.un.org/SDGAPI/v1/sdg/Series/"+s+"/Dimensions")
            dims = json.loads(dims_req.content)
            # print(dims)
            # generate full list of dims
            full_dims_c = []
            full_dims_d = []
            # look for a dim in dims
            for d_a in dim_aggrs[s]:
                list_codes = [element for element in dims if element['id'] == d_a]
                codes = list_codes[0]['codes']
                # create list of codes and list of  
                loc = [element['code'].rstrip() for element in codes if element['code'].rstrip() not in codes_ignore]
                lod = [element['description'].rstrip() for element in codes if element['code'].rstrip() not in codes_ignore]
                full_dims_c.append(loc)
                full_dims_d.append(lod)
            # now let's prepare list of possible combinations
            l_dims_c = list(itertools.product(*full_dims_c))
            l_dims_d = list(itertools.product(*full_dims_d))
            for j, c in enumerate(l_dims_c):
                var_name = s + '_' + '_'.join(c)
                var_desc = d + ', ' + ', '.join(l_dims_d[j])
                UNSTAT_meta.append({'code': var_name,
                                    'name': var_desc,
                                    'source': 'UNSTAT Global SDG Indicators Database',
                                    'metadata': 'https://unstats.un.org/wiki/display/SDGeHandbook/Indicator+' + indicator})
        else:
            UNSTAT_meta.append({'code': s,
                                'name': d,
                                'source': 'UNSTAT Global SDG Indicators Database',
                                'metadata': 'https://unstats.un.org/wiki/display/SDGeHandbook/Indicator+' + indicator})
        if verbose:
            print(progress_bar(i+1, n_series, l=15))
    return UNSTAT_meta


def load_series_list(force_download = False, save_json = True, json_name = "SDG_Series_List.json", verbose = False):
    """
    Get list of series from https://unstats.un.org/SDGAPI/v1/sdg/Series/List?allreleases=false
    force_download force download from servers
    save_json save json in current dir with name json_name
    """
    if os.path.isfile(json_name) and not force_download:
        # Load from file
        if verbose:
            print("Loading series json from file %s" % json_name)
        with open(json_name, "r") as f:
            series = json.load(f)
    else:
        # Download it from server
        if verbose:
            print("Getting series json from web https://unstats.un.org/SDGAPI/v1/sdg/Series/List?allreleases=false")
        series_req = try_get("https://unstats.un.org/SDGAPI/v1/sdg/Series/List?allreleases=false", verbose = verbose)
        if series_req['code']=="Ok":
            series = json.loads(series_req['result'].content.decode('UTF-8'))
        else:
            series = []
    if save_json and (not os.path.isfile(json_name) or force_download):
        if verbose:
            print("Writing series json to file %s" % json_name)
        with open(json_name, 'w', encoding='utf-8') as f:
            json.dump(series, f, ensure_ascii=False, indent=4)
    return series

def get_dims(series_code, dim_ignore=[]):
    # Get list of dimensions for a series and ignore those in list   
    dim_url = "https://unstats.un.org/SDGAPI/v1/sdg/Series/"+series_code+"/Dimensions"
    dim_req = requests.get(dim_url)
    dim = json.loads(dim_req.content)
    dim_list = [i['id'] for i in dim if i['id'] not in dim_ignore]
    return dim_list

def load_series_data(series_code, countries=[1], save_tsv=True, code_inc_dims=[]):
    """
    Loads series for list of countries. Include in series code dimensions listed in code_inc_dims. Dump results into csv file if save_csv
    """
    if os.path.isfile(".\\Data\\" + series_code + ".tsv"):
        return 1
    f_tsv = open(".\\Data\\" + series_code + ".tsv", "w")
    f_big = open(".\\Data\\UNSTAT-ALL-DATA.tsv", "a")
    for c in countries:
        url = "https://unstats.un.org/SDGAPI/v1/sdg/Series/" + series_code + "/GeoArea/" + str(c) + "/DataSlice"
        try_rec = try_get(url)
        if try_rec['code'] == "Ok":
            req = try_rec['result']
        else:
            print("Something went wrong getting %s for %s: %s" % (series_code, M49_ISO.get(c), try_rec['result']))
            req = try_rec['result'] 
        if req.status_code == 200:
            data = json.loads(req.content)
            c_ISO = M49_ISO.get(c)
            for d in data['dimensions']:
                # print(d)
                series_unique=series_code
                for cid in code_inc_dims:
                    if cid in d.keys():
                        series_unique = series_unique + "_" + d[cid].strip()
                    else:
                        print("! Warning, %s doesn't has dimension %s" %(series_code, cid))
                write_str = "{}\t{}\t{}\t{}\t{}\n".format(c_ISO,
                                                          series_unique,
                                                          d['timePeriodStart'],
                                                          d['value'], [(k, d[k]) for k in d.keys() if k not in data_fields])
                f_tsv.write(write_str)
                f_big.write(write_str)
        else:
            print('Something went wrong...')
    f_tsv.close()
    f_big.close()
    return 0


dim_ignore = ['Reporting Type']
data_fields = ['value', 'timePeriodStart', 'Reporting Type']

# KAZ + OECD Countries + Central Asia
countries=[398,  36,  40,  56, 124, 152, 203, 208, 233, 246, 250, 276, 300,
           348, 352, 372, 376, 380, 392, 410, 428, 440, 442, 484, 528, 554,
           578, 616, 620, 703, 705, 724, 752, 756, 792, 826, 840, 417, 762,
           795, 860]

# Goals to load. If list is empty -- load all goals, else list goals to load
goals_to_load = ["1", "17"]
# goals_to_load = []

dim_aggrs = {'AG_FPA_COMM': ['Type of product'],
'EG_ELC_ACCS': ['Location'],
'EN_ATM_PM25': ['Location'],
'EN_MAT_DOMCMPC': ['Type of product'],
'EN_MAT_DOMCMPG': ['Type of product'],
'EN_MAT_DOMCMPT': ['Type of product'],
'EN_MAT_FTPRPC': ['Type of product'],
'EN_MAT_FTPRPG': ['Type of product'],
'EN_MAT_FTPRTN': ['Type of product'],
'EN_REF_WASCOL': ['Cities'],
'ER_H2O_IWRMD': ['Level/Status'],
'ER_H2O_IWRMP': ['Level/Status'],
'ER_H2O_PARTIC': ['Location'],
'ER_H2O_PRDU': ['Location'],
'ER_H2O_PROCED': ['Location'],
'ER_H2O_RURP': ['Location'],
'ER_WAT_PARTIC': ['Location'],
'FB_BNK_ACCSS': ['Sex'],
'IS_RDP_FRGVOL': ['Mode of transportation'],
'IS_RDP_PFVOL': ['Mode of transportation'],
'IT_MOB_NTWK': ['Type of mobile technology'],
'IT_MOB_OWN': ['Sex'],
'IT_NET_BBN': ['Type of speed'],
'IT_NET_BBP': ['Type of speed'],
'IU_COR_BRIB': ['Sex'],
'SE_ACC_COMP': ['Education level'],
'SE_ACC_DWAT': ['Education level'],
'SE_ACC_ELEC': ['Education level'],
'SE_ACC_HNWA': ['Education level'],
'SE_ACC_INTN': ['Education level'],
'SE_ACC_SANI': ['Education level'],
'SE_ADT_ACTS': ['Sex', 'Type of skill'],
'SE_ADT_EDUCTRN': ['Sex'],
'SE_ADT_FUNS': ['Age', 'Sex', 'Type of skill'],
'SE_GPI_FUNPROF': ['Type of skill'],
'SE_GPI_ICTS': ['Type of skill'],
'SE_GPI_MATACH': ['Education level'],
'SE_GPI_REAACH': ['Education level'],
'SE_GPI_TRATEA': ['Education level'],
'SE_IMP_FPOF': ['Type of skill'],
'SE_INF_DSBL': ['Education level'],
'SE_LGP_ACHIMA': ['Education level'],
'SE_LGP_ACHIRE': ['Education level'],
'SE_MAT_PROF': ['Sex', 'Education level'],
'SE_NAP_ACHIMA': ['Education level'],
'SE_NAP_ACHIRE': ['Education level'],
'SE_PRE_PARTN': ['Sex'],
'SE_REA_PROF': ['Sex', 'Education level'],
'SE_SEP_FUNPROF': ['Type of skill'],
'SE_SEP_MATACH': ['Education level'],
'SE_SEP_REAACH': ['Education level'],
'SE_TRA_GRDL': ['Sex', 'Education level'],
'SE_URP_MATACH': ['Education level'],
'SE_URP_REAACH': ['Education level'],
'SG_CPA_MIGR': ['Policy Domains'],
'SG_CPA_MIGRP': ['Policy Domains'],
'SG_GEN_LOCGELS': ['Sex'],
'SG_GEN_PARL': ['Sex'],
'SG_GEN_PARLN': ['Sex'],
'SG_GEN_PARLNT': ['Sex'],
'SG_INT_MBRDEV': ['Name of international institution'],
'SG_INT_VRTDEV': ['Name of international institution'],
'SH_DTH_NCOM': ['Sex'],
'SH_DTH_RNCOM': ['Sex', 'Name of non-communicable disease'],
'SH_DYN_IMRT': ['Sex'],
'SH_DYN_IMRTN': ['Sex'],
'SH_DYN_MORT': ['Sex'],
'SH_DYN_MORTN': ['Sex'],
'SH_DYN_NMRT': ['Sex'],
'SH_DYN_NMRTN': ['Sex'],
'SH_H2O_SAFE': ['Location'],
'SH_HIV_INCD': ['Age', 'Sex'],
'SH_IHR_CAPS': ['IHR Capacity'],
'SH_MED_HEAWOR': ['Type of occupation'],
'SH_PRV_SMOK': ['Sex'],
'SH_SAN_DEFECT': ['Location'],
'SH_SAN_HNDWSH': ['Location'],
'SH_SAN_SAFE': ['Location'],
'SH_STA_POISN': ['Sex'],
'SH_STA_SCIDE': ['Sex'],
'SH_STA_SCIDEN': ['Sex'],
# 'SH_STA_WASH': ['Sex'],
'SI_COV_BENFTS': ['Sex'],
'SI_COV_CHLD': ['Sex'],
'SI_COV_DISAB': ['Sex'],
'SI_COV_MATNL': ['Sex'],
'SI_COV_PENSN': ['Sex'],
'SI_COV_POOR': ['Sex'],
'SI_COV_UEMP': ['Sex'],
'SI_COV_VULN': ['Sex'],
'SI_COV_WKINJRY': ['Sex'],
'SI_POV_EMP1': ['Age', 'Sex'],
'SI_POV_NAHC': ['Location'],
'SL_DOM_TSPD': ['Location', 'Age', 'Sex'],
'SL_DOM_TSPDCW': ['Location', 'Age', 'Sex'],
'SL_DOM_TSPDDC': ['Location', 'Age', 'Sex'],
'SL_EMP_AEARN': ['Sex', 'Type of occupation'],
'SL_EMP_FTLINJUR': ['Sex', 'Migratory status'],
'SL_EMP_INJUR': ['Sex', 'Migratory status'],
'SL_ISV_IFRM': ['Sex'],
'SL_TLF_CHLDEA': ['Age', 'Sex'],
'SL_TLF_CHLDEC': ['Age', 'Sex'],
'SL_TLF_NEET': ['Age', 'Sex'],
'SL_TLF_UEM': ['Age', 'Sex'],
'SL_TLF_UEMDIS': ['Disability status', 'Sex'],
'SP_ACS_BSRVH2O': ['Location'],
'SP_ACS_BSRVSAN': ['Location'],
'TM_TAX_ATRFD': ['Tariff regime (status)', 'Type of product'],
'TM_TAX_WWTAV': ['Tariff regime (status)', 'Type of product'],
'TM_TRF_ZERO': ['Type of product'],
'VC_HTF_DETV': ['Age', 'Sex'],
'VC_HTF_DETVFL': ['Age', 'Sex'],
'VC_HTF_DETVOG': ['Age', 'Sex'],
'VC_HTF_DETVOP': ['Age', 'Sex'],
'VC_HTF_DETVSX': ['Age', 'Sex'],
'VC_IHR_PSRC': ['Sex'],
'VC_IHR_PSRCN': ['Sex'],
'VC_PRR_PHYV': ['Sex'],
'VC_PRR_ROBB': ['Sex'],
'VC_PRR_SEXV': ['Sex'],
'VC_VAW_MARR': ['Age'],
'VC_VAW_MTUHRA': ['Sex'],
'VC_VAW_SXVLN': ['Sex'],
'VC_VOV_PHYL': ['Sex'],
'VC_VOV_ROBB': ['Sex'],
'VC_VOV_SEXL': ['Sex'],
### New disaggregates available in January 2020
'SI_HEI_TOTL': ['Quantile'],
'SI_COV_SOCAST': ['Quantile'],
'SI_COV_SOCINS': ['Quantile'],
'SI_COV_LMKT':['Quantile'],
'SE_TOT_PRFL': ['Sex', 'Education level', 'Type of skill'],
'SE_NAP_ACHI': ['Education level', 'Type of skill'],
'SE_LGP_ACHI': ['Education level', 'Type of skill'],
'SE_TOT_GPI': ['Education level', 'Type of skill'],
'SE_TOT_SESPI': ['Education level', 'Type of skill'],
'TM_TAX_WMFN': ['Type of product'],
'TM_TAX_WMPS': ['Type of product'],
'TM_TAX_DMFN': ['Type of product'],
'TM_TAX_DPRF': ['Type of product']             
}


# Load M49 and ISO codes for countries
if os.path.isfile("M49-ISO.txt"):
    M49_ISO = {}
    with open("M49-ISO.txt", "r") as f:
        for line in f:
            codes = re.split(r'\t', line)
            M49_ISO[int(codes[0])] = codes[1].strip()
else:
    M49_ISO = {1: "World"}

series = load_series_list()

n_series = len(series)
# Load series 
for i, s in enumerate(series):
    # Check if we need to load this series, if it is in goal list
    load_this_series = False
    if goals_to_load==[]:
        load_this_series = True
    else:
        for g in s['goal']:
            if g in goals_to_load:
                load_this_series = True
    if load_this_series:
        cid = dim_aggrs.get(s['code']) if s['code'] in dim_aggrs.keys() else []
        print("Loading {}, dims {}".format(s['code'], cid))
        print(load_series_data(series_code = s['code'], countries=countries, save_tsv=True, code_inc_dims=cid))
        print(progress_bar(i+1, n_series, 33))

# Generate series names with disaggregations
UNSTAT_meta = get_UNSTAT_meta(series, verbose)
with open("UNSTAT_series_list.json", 'w', encoding='utf-8') as f:
    json.dump(UNSTAT_meta, f, ensure_ascii=False, indent=4)
full_list =[]
full_list.extend(UNSTAT_meta)
with open("Series.Metadata.CSV", "w", encoding="utf-8") as f:
    f.write(f'"code","name","source","metadata"\n')
    for s in full_list:
        code = s['code']
        name = s['name']
        source = s['source']
        metadata = s['metadata']
        f.write(f'"{code}","{name}","{source}","{metadata}"\n')

