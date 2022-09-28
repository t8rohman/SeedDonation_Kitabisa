import pandas as pd
from datetime import datetime
import json
import time
from pathlib import Path  

from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # to run selenium in background
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def donor_scraper_cont(donation_id, url_index, flpath):
    '''
    function to scrape list of all donors from a donation
    url: url of the last scraping data
    flpath: path to save the scrapped data
    '''
    
    # filepath_num for the iteration
    # next to append next page, filled an initial value to not trigger the while loop
    next = 'trigger' 
    filepath_num = 0
    donation_id = 'donasitahfidzqu'
    url = 'view-source:https://core.kitabisa.com/campaigns/' + donation_id + '/donors?sort=verified&'  
    url_init = 'view-source:https://core.kitabisa.com/campaigns/' + donation_id + '/donors?sort=verified&next=' + url_index
    url_new = url
    df_appended = pd.DataFrame()
    i = 0  # to trigger the if statement for the driver to go to the next url
    
    while next != '':
        try:
            chrome_options = Options()
            # hide the chrome ui when running the webdriver
            chrome_options.add_argument("--headless")  
            chrome_options.add_argument("--window-size=1920,1080")
            # user agent to avoid the web incorrectly read the user agent as a headless browser
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36' 
            chrome_options.add_argument(f'user-agent={user_agent}')

            driver = webdriver.Chrome(ChromeDriverManager().install(),
                                      options=chrome_options)  # to bypass the problem in missing path of webdriver

            if i == 0:
                driver.get(url_init)
                i = i + 1
            else:
                driver.get(url_new)
            
            content = driver.page_source
            content = driver.find_element_by_class_name('line-content').text
            # print(content)  # turned off as it makes crash if we scrape a lot of data
            driver.quit()

            data = json.loads(content)  # this is the json data for the list of the donors
        
            df = pd.json_normalize(data, record_path=['data'])
            df['time_scrapped']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df['short_url'] = donation_id
            df_appended = df_appended.append(df)
            # print(df_appended) -> turned off as it makes crash if we scrape a lot of data
            
            filepath_num = filepath_num + 1
            filepath = Path(flpath +  donation_id + '_donorsinfo' + '_' + str(filepath_num) +'.csv')  
            filepath.parent.mkdir(parents=True, exist_ok=True)  
            df.to_csv(filepath, index=False)
            
            next = data['next']
            url_new = url + 'next=' + next
            
            # debuggers to see which files we already read
            with open(f'{flpath}logreader_debug.txt', 'a') as fh:
                print('succesfully read ' + next, file=fh)
            
        except:
            # debuggers to see which files went to error
            with open(f'{flpath}logreader_debug.txt', 'a') as fh:
                print('error when reading ' + next, file=fh)
            pass    
            
    filepath = Path(flpath +  donation_id + '_donorsinfo_appended.csv')  
    filepath.parent.mkdir(parents=True, exist_ok=True)  
    df_appended.to_csv(filepath, index=False)
    print('Sucessfully read all the donors information.')
    
donation_id = 'donasitahfidzqu'
url_index = '79863959_1654215907'
flpath = '/Users/mac/Documents/RU/THESIS/working_thesis/pilot_data_2/temp/donasitahfidzqu-cont/'
donor_scraper_cont(donation_id, url_index, flpath)