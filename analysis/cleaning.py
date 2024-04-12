import pandas as pd


def clean_donors(df, save_path):
    '''
    Function for cleaning the donors list file, dropping all variables that are not listed on the website interface.

    Parameters:
    - df (DataFrame): DataFrame including all of the donors.
    - save_path (str): Where to save the DataFrame as a CSV file.
    
    Returns:
    - DataFrame: Cleaned DataFrame.
    '''
    columns = ['id', 'is_anonymous', 'user.string', 'amount', 'created', 'time_scrapped', 'short_url']  # only taking the important columns
    df = df.loc[:, columns]
    df = df.rename(columns={'created': 'created_unix'})  
    df['created_ts'] = pd.to_datetime(df['created_unix'], unit='s')  # convert unix timestamp to utc timestamp
    df = df[['id', 'is_anonymous', 'user.string', 'amount', 'created_unix', 'created_ts', 'time_scrapped', 'short_url']]  # rearrange the columns
    
    print(df.head(5))
    df.to_csv(save_path, index=False)
    return df
    

def clean_donation(df, save_path):
    '''

    Function for cleaning the campaigns list file, including only relevant variables for the analysis.

    Parameters:
    - df (DataFrame): DataFrame including all of the campaigns.
    - save_path (str): Where to save the DataFrame as a CSV file.
    
    Returns:
    - DataFrame: Cleaned DataFrame.
    '''
    columns = ['id', 'short_url', 'is_forever_running', 'is_open_goal', 'donation_received', 'donation_count', 
               'donation_target', 'donation_percentage', 'campaign_start', 'campaign_last_update', 'days_remaining', 
               'is_open_for_donation', 'is_verified', 'campaigner.type', 'category.name', 'time_scraped']
    df = df.loc[:, columns]
    df['start_ts_utc'] = pd.to_datetime(df['campaign_start'], unit='s')
    df['last_ts_utc'] = pd.to_datetime(df['campaign_last_update'], unit='s')
    df['days_running'] = (df['last_ts_utc'] - df['start_ts_utc']).dt.days
    df['days_duration'] = df['days_running'] +  df['days_remaining']

    # arrange the column again
    columns_arranged = ['id', 'short_url', 'is_forever_running', 'is_open_goal', 'donation_received', 'donation_count', 'donation_target',
                        'donation_percentage', 'start_ts_utc', 'last_ts_utc', 'days_running', 'days_remaining', 'days_duration', 'is_open_for_donation', 
                        'is_verified', 'campaigner.type', 'category.name', 'time_scraped'] 
    df = df[columns_arranged]
    
    print(df.head(5))
    df.to_csv(save_path, index=False)
    return df