'''
all the modules needed to scrape donors and donation list from kitabisa.

donor_scraper(): scrape list of all donors from a donation
donation_scraper(): function to scrape all of the information about the donation
donationlist_scraper(): to parse all the donation index from the parent page
donor_scraper_ind(): scrape only individual donor set, used when we got error
donationprop_scraper_to_dataframe(): scrape all the donation information from a donation list
'''


import pandas as pd
from datetime import datetime
import json
import time
from pathlib import Path  

from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # to run selenium in background
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def donor_scraper(donation_id, flpath):
    '''
    function to scrape list of all donors from a donation
    donatio_id: donor short name, take the donor from the url
    flpath: path to save the scrapped data
    '''
    
    # filepath_num for the iteration
    # next to append next page, filled an initial value to not trigger the while loop
    next = 'trigger' 
    filepath_num = 0
    url = 'view-source:https://core.kitabisa.com/campaigns/' + donation_id + '/donors?sort=verified&'  
    url_new = url
    df_appended = pd.DataFrame()
    
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
        
            driver.get(url_new)
            
            content = driver.page_source
            content = driver.find_element_by_class_name('line-content').text
            # print(content) -> turned off as it makes crash if we scrape a lot of data
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
                print('succesfully read ' + donation_id + ' ' + next, file=fh)
            
        except:
            # debuggers to see which files went to error
            with open(f'{flpath}logreader_debug.txt', 'a') as fh:
                print('error when reading ' + donation_id + ' ' + next, file=fh)
            pass    
            
    filepath = Path(flpath +  donation_id + '_donorsinfo_appended.csv')  
    filepath.parent.mkdir(parents=True, exist_ok=True)  
    df_appended.to_csv(filepath, index=False)
    print('Sucessfully read all the donors information.')


def donation_scraper(donation_id, flpath):
    '''
    function to scrape all of the information about the donation
    donatio_id: donor short name, take the donor from the url
    flpath: path to save the scrapped data
    '''
    
    url = 'view-source:https://kitabisa.com/campaign/' + donation_id
    
    # scrape all the html page source as webdriver couldn't interact with hidden script
    # we're going to scrape the hidden script that contains the information about the donation
    driver = webdriver.Chrome(ChromeDriverManager().install())  # to bypass the problem in missing path of webdriver
    driver.get(url)
    content = driver.page_source
    driver.quit()

    # only parse the json file from the html, the hidden script
    # start and the end is the html structure from kitabisa, DO NOT CHANGE at all
    start = '__NEXT_DATA__</span>" <span class="html-attribute-name">type</span>="<span class="html-attribute-value">application/json</span>"&gt;</span>'
    end = '<span class="html-tag">&lt;/script&gt;</span><span class="html-tag">&lt;script <span class="html-attribute-name">src</span>'
    json_script = content.split(start)[1].split(end)[0]
    
    json_format = json.loads(json_script)
    df = pd.json_normalize(json_format['props']['pageProps']['campaign'])
    df['time_scraped'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    filepath = Path(flpath + donation_id + '_donationinfo.csv')  # modify later by the name of donation  
    filepath.parent.mkdir(parents=True, exist_ok=True)  
    df.to_csv(filepath, index=False)
    
    print("Successfully scrape the data to a CSV file.")
    

def donationlist_scraper(url, num_scroll, flpath):
    '''
    to parse all the donation index from the parent page.
    copy the page from this https://kitabisa.com/explore/all, and their child pages (category of donation).
    url: url of kitabisa page. navigate from home, and choose which category we're interested to see
    num_scroll: how many times we want to scroll the page, as the page is infinite-scroll format
    '''
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)
    time.sleep(2)
    scroll_pause_time = 1  # change pause time to load all the content of the page, this parameter will be used for time.sleep
    screen_height = driver.execute_script("return window.screen.height;")
    df_donation = pd.DataFrame()
    i = 1
    r = 0

    # code used to automatically scroll the infinite-scroll page
    while True:
        driver.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))
        i = i + 1
        time.sleep(scroll_pause_time)  # refer to scroll_pause_time outside the while loop
        scroll_height = driver.execute_script("return document.body.scrollHeight;")  
        if i == num_scroll:  # how many times we want to scroll the page
            break 

    content = driver.page_source
    driver.quit()
    
    soup = BeautifulSoup(content, "html.parser")
    donation_list = []
    
    # find all the campaign short url and append it to df_donation
    for don in soup.find_all('a', href=True):
        # print("Found the campaign index:", don['href'])
        donation = don['href']
        if "campaign/" in donation:
            donation = donation.split("campaign/")[1]
            df_donation.loc[r, 'short_url'] = donation
        r = r + 1
    df_donation.reset_index(drop=True, inplace=True)
    
    r = 0
    # find all the campaign name and append it to df_donation
    for don in soup.find_all("div", {"class": "cardStyle__CardSubtitle-sc-__sc-1rj3uct-1 kfhTie"}):
        don = don.text
        df_donation.loc[r, 'donation_org'] = don
        r = r + 1
    
    r = 0
    # find all the campaign organizer and append it to df_donation
    for don in soup.find_all("div", {"class": "style__ListContent-sc-__sc-1sl4ulh-4 fGPGGA"}):
        don = don.text
        df_donation.loc[r, 'donation_name'] = don
        r = r + 1
    
    r = 0
    # find all the campaign total donation and append it to df_donation
    for don in soup.find_all("div", {"class": "style__ListCountItem-sc-__sc-1sl4ulh-6 izOCxs"}):
        don = don.text
        don = don.replace('TerkumpulRp ', '')
        don = don.replace('.', '')
        df_donation.loc[r, 'donation_received'] = don
        r = r + 1
       
    r = 0    
    # find all the campaign days remaining and append it to df_donation
    for don in soup.find_all("div", {"class": "style__ListCountItem-sc-__sc-1sl4ulh-6 jwEHoD"}):
        don = don.text
        don = don.replace('Sisa hari', '')
        df_donation.loc[r, 'days_to_go'] = don
        r = r + 1
    
    df_donation['time_scraped'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    today = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    filepath = Path(flpath + 'donation_list_' + today + '_.csv')  
    filepath.parent.mkdir(parents=True, exist_ok=True)  
    df_donation.to_csv(filepath, index=False)

    print("Successfully scrape the data to a CSV file.")
    
    return df_donation


def donor_scraper_ind(link, flpath):
    '''
    function to scrape a donor from a which got an error message
    link: complete url of the error file
    flpath: path to save the scrapped data
    '''
    
    # set variables needed for the function
    start_url = 'https://core.kitabisa.com/campaigns/'
    end_url = '/donors?sort=verified&next=87644292_1662247648'
    donation_id = link.split(start_url)[1].split(end_url)[0]
    
    url = 'view-source:' + link  
    url_new = url
    df_appended = pd.DataFrame()
    
    # using webdriver to read the data
    driver = webdriver.Chrome(ChromeDriverManager().install())  # to bypass the problem in missing path of webdriver

    driver.get(url_new)
    content = driver.page_source
    content = driver.find_element_by_class_name('line-content').text
    driver.quit()

    data = json.loads(content)  # this is the json data for the list of the donors
    print(data)
        
    df = pd.json_normalize(data, record_path=['data'])
    df['time_scrapped']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df['short_url'] = donation_id
    df_appended = df_appended.append(df)
    print(df_appended)  # to check the data while it's running

    filepath = Path(flpath +  donation_id + '_errordonors.csv')  
    filepath.parent.mkdir(parents=True, exist_ok=True)  
    df.to_csv(filepath, index=False)
    
    print('Sucessfully read the donors information.')


def donationprop_scraper_to_dataframe(donation_list, flpath):
    '''
    function to scrape all of the information about the donation from a list
    donation_list: list of donation, should be in format of LIST
    flpath: path to save the scrapped data
    '''
    df_donations_prop = pd.DataFrame()
    
    for donation_id in donation_list:
        try:
            url = 'view-source:https://kitabisa.com/campaign/' + donation_id
    
            chrome_options = Options()
            # hide the chrome ui when running the webdriver
            chrome_options.add_argument("--headless")  
            chrome_options.add_argument("--window-size=1920,1080")
            # user agent to avoid the web incorrectly read the user agent as a headless browser
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36' 
            chrome_options.add_argument(f'user-agent={user_agent}')

            driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)  # to bypass the problem in missing path of webdriver
        
            driver.get(url)
            content = driver.page_source
            driver.quit()

            # only parse the json file from the html, the hidden script
            # start and the end is the html structure from kitabisa, DO NOT CHANGE at all
            start = '__NEXT_DATA__</span>" <span class="html-attribute-name">type</span>="<span class="html-attribute-value">application/json</span>"&gt;</span>'
            end = '<span class="html-tag">&lt;/script&gt;</span><span class="html-tag">&lt;script <span class="html-attribute-name">src</span>'
            json_script = content.split(start)[1].split(end)[0]
    
            json_format = json.loads(json_script)
            df = pd.json_normalize(json_format['props']['pageProps']['campaign'])
            df['time_scraped'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("Successfully scrape donation from " + donation_id + ". Going to scrape the next donation.")

            df_donations_prop = df_donations_prop.append(df)
            
            # debuggers to see which files we already read
            with open(f'{flpath}logreader_debug.txt', 'a') as fh:
                print('succesfully read ' + donation_id, file=fh)
        
        except:
            # debuggers to see which files went to error
            print("Error when scraping donation from " + donation_id + ". Going to scrape the next donation.")
            with open(f'{flpath}logreader_debug.txt', 'a') as fh:
                print('error when reading ' + donation_id, file=fh)
                pass
            
    today = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    filepath = Path(flpath + 'donation_list_with_prop_' + today + '_.csv')
    filepath.parent.mkdir(parents=True, exist_ok=True)  
    df_donations_prop.to_csv(filepath, index=False)
    print("Process done! Check the log file to see if we successfully read the data.")
    
    return df_donations_prop


def donor_scraper_cont(donation_id, url_index, flpath):
    '''
    function to scrape donors if the donor_scraper function is interrupted in the middle of scraping
    donation_id: short url of the donation
    url_index: the index of last files read by the donor_scraper function
    flpath: where to save the file (remember not to save it in the same destination with the previous scraped file)
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
            filepath = Path(flpath +  donation_id + '_donorsinfo_cont_' + str(filepath_num) +'.csv')  
            filepath.parent.mkdir(parents=True, exist_ok=True)  
            df.to_csv(filepath, index=False)
            
            next = data['next']
            url_new = url + 'next=' + next
            
            # debuggers to see which files we already read
            with open(f'{flpath}logreader_debug.txt', 'a') as fh:
                print('succesfully read ' + donation_id + ' ' + next, file=fh)
            
        except:
            # debuggers to see which files went to error
            with open(f'{flpath}logreader_debug.txt', 'a') as fh:
                print('error when reading ' + donation_id + ' ' + next, file=fh)
            pass    
            
    filepath = Path(flpath +  donation_id + '_donorsinfo_appended.csv')  
    filepath.parent.mkdir(parents=True, exist_ok=True)  
    df_appended.to_csv(filepath, index=False)
    print('Sucessfully read all the donors information.')