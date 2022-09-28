import pandas as pd
from datetime import datetime


def clean_donors(open_path, save_path):
    df = pd.read_csv(open_path)
    columns = ['id', 'is_anonymous', 'amount', 'created', 'time_scrapped', 'short_url']  # only taking the important columns
    df = df.loc[:, columns]
    df = df.rename(columns={'created': 'created_unix'})  
    df['created_ts'] = pd.to_datetime(df['created_unix'], unit='s')  # convert unix timestamp to utc timestamp
    df = df[['id', 'is_anonymous', 'amount', 'created_unix', 'created_ts', 'time_scrapped', 'short_url']]  # rearrange the columns
    
    print(df.head(5))
    df.to_csv(save_path, index=False)
    return df
    

def clean_donation(open_path, save_path):
    df = pd.read_csv(open_path)
    columns = ['id', 'short_url', 'is_forever_runing', 'is_open_goal', 'donation_received', 'donation_count', 
               'donation_target', 'donation_percentage', 'campaign_start', 'days_running', 'days_remaining', 
               'is_zakat', 'is_instant_zakat', 'is_open_for_donation', 'is_verified', 'is_optimized_by_ads',
               'status.name', 'campaigner.is_verified', 'campaigner.type', 'category.name', 'time_scraped']
    df = df.loc[:, columns]
    df = df.rename(columns={'campaign_start': 'start_ts_unix'})  
    df['start_ts_utc'] = pd.to_datetime(df['start_ts_unix'], unit='s')
    df['days_duration'] = df['days_running'] + df['days_remaining']
    
    # arrange the column again
    columns_arranged = ['id', 'short_url', 'is_forever_runing', 'is_open_goal', 'donation_received', 'donation_count', 'donation_target',
                        'donation_percentage', 'start_ts_unix', 'start_ts_utc', 'days_duration', 'days_running', 'days_remaining', 'is_zakat', 
                        'is_instant_zakat', 'is_open_for_donation', 'is_verified', 'is_optimized_by_ads', 'status.name', 'campaigner.is_verified', 
                        'campaigner.type', 'category.name', 'time_scraped'] 
    df = df[columns_arranged]
    
    print(df.head(5))
    df.to_csv(save_path, index=False)
    return df

