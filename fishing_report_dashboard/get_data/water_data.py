import re
import requests
from io import StringIO
from datetime import datetime

import pandas as pd

from utils import c_to_f


def _get_url(site, param_cd, start_dt, end_dt):
    url_base = 'https://waterservices.usgs.gov/nwis/iv/'
    url_params_ind = '?'
    url_params = f'sites={site}&parameterCd={param_cd}&startDT={start_dt}&endDT={end_dt}&siteStatus=all&format=rdb'
    
    return url_base + url_params_ind + url_params


def _clean_text_data(text):
    clean_tsv = ''
    for line in text.splitlines():
        if not line.startswith('#'):
            clean_tsv += line + '\n'

    return clean_tsv


def _read_usgs_tsv(tsv):
    
    return pd.read_csv(StringIO(tsv), sep='\t', lineterminator='\n', skiprows=[1])


def _verify(text):
    status = True
    
    if 'The request sent by the client was syntactically incorrect' in text:
        print('A parameter was likely mistyped.')
        status = False
        
    elif 'No sites found matching' in text:
        print('The site doesn\'t measure the provided parameter.')
        status = False
    
    return status


def _get_param(param_cd):
    param_dict = {
        '00010' : 'temperature',
        '00050' : 'height'
    }
    
    return param_dict[param_cd]


def _transform_df(df, param_cd):
    # convert column type to datetime
    df['datetime'] = df['datetime'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M'))
    
    # dropping column, renaming column from param_cd to actual parameter
    for c in df.columns:
        
        # drop unnecessary column
        if re.search('\d+_\d+_cd', c):
            drop_col = re.match('\d+_\d+_cd', c).string
            df = df.drop(drop_col, axis = 1)
            
        # rename param_cd column to param name
        elif re.search('\d+_\d+$', c):
            rnm_col = re.match('\d+_\d+$', c).string
            param_nm = _get_param(param_cd)
            df = df.rename(columns={rnm_col: param_nm})
            
            # convert Celcius to Fahrenheit
            if param_cd == '00010':
                df[param_nm] = df[param_nm].apply(lambda x: c_to_f(x))
                
    df = df.rename(columns = {'temperature' : 'water_temp'})
    
    return df
            

def get_usgs_water_data(site, param_cd, start_dt, end_dt):
    r = requests.get(_get_url(site, param_cd, start_dt, end_dt))
    raw_tsv = r.text
    if _verify(raw_tsv):
        cleaned_tsv = _clean_text_data(raw_tsv)
        df = _read_usgs_tsv(cleaned_tsv)
        df = _transform_df(df, param_cd)
    else:
        df = None
    
    return df