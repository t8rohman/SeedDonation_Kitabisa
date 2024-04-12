import pandas as pd
import json
import time
import os
import math
from datetime import datetime
from pathlib import Path  

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


class Scraper:
    '''
    A class to scrape projects data from Kitabisa homepage using Selenium and BeautifulSoup.

    Attributes:
    - url (str): The URL of the website to scrape.
    - num_scroll (int): The number of times to scroll the page to load all content.
    - save_path (str): The file path to save the scraped data.
    - driver: The Selenium WebDriver object for interacting with the website.
    '''

    def __init__(self, save_path):
        '''
        Initialize the Scraper object with the given URL, number of scrolls, and file path.

        Args:
        - save_path (str): The file path to save the scraped data.
        '''
        self.save_path = save_path
        self.driver_projectlist = None
        self.driver_projectprops = None

    def __enter__(self):
        '''
        Enter method to initialize the Selenium WebDriver when used in a 'with' statement.
        '''
        # driver for kitabisa homepage -> didn't allow us to read the page with a headless
        self.driver_projectlist = webdriver.Chrome()

        # driver for projects information -> use headless to fasten the scraping process
        chrome_options = Options()
        # hide the chrome ui when running the webdriver
        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--window-size=1920,1080")
        # user agent to avoid the web incorrectly read the user agent as a headless browser
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36' 
        chrome_options.add_argument(f'user-agent={user_agent}')
        self.driver_projectprops = webdriver.Chrome(options=chrome_options)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        '''
        Exit method to close the Selenium WebDriver when exiting the 'with' statement.
        '''
        self.driver_projectlist.quit()
        self.driver_projectprops.quit()

    def projectlist_scrape(self, url, num_scroll):
        '''
        Scrape list of projects data from the homepage using Selenium and BeautifulSoup.

        Args:
        - url (str): The URL of the website to scrape.
        - num_scroll (int): The number of times to scroll the page to load all content.

        Returns:
        - df_projects (pd.DataFrame): A DataFrame containing the scraped data.
        '''
        self.driver_projectlist.get(url)
        time.sleep(2)
        scroll_pause_time = 1  
        screen_height = self.driver_projectlist.execute_script("return window.screen.height;")
        df_projects = pd.DataFrame()
        i = 1
        r = 0

        while True:
            self.driver_projectlist.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))
            i = i + 1
            time.sleep(scroll_pause_time)
            scroll_height = self.driver_projectlist.execute_script("return document.body.scrollHeight;")  
            if i == num_scroll:
                break 

        content = self.driver_projectlist.page_source
    
        soup = BeautifulSoup(content, "html.parser")

        # change this accordingly later based on the dynamics of Kitabisa
        div_class_projectorg = 'my-[0.25em] mx-[0em] flex w-full items-center align-middle text-xs text-[rgba(0,0,0,0.9)]'
        div_class_projectname = 'my-[0.25em] mx-[0em] overflow-hidden break-words text-sm font-semibold text-tundora'
        div_class_donationreceived = 'flex flex-col'
        div_class_daystogo = 'flex flex-col text-right'

        # find all the campaign short url and append it to df_donation
        for don in soup.find_all('a', href=True):
            # print("Found the campaign index:", don['href'])
            donation = don['href']
            if "campaign/" in donation:
                donation = donation.split("campaign/")[1]
                df_projects.loc[r, 'short_url'] = donation
            r = r + 1
        df_projects.reset_index(drop=True, inplace=True)
        
        r = 0
        # find all the campaign name and append it to df_donation
        for don in soup.find_all("div", {"class": div_class_projectorg}):
            don = don.text
            df_projects.loc[r, 'project_org'] = don
            r = r + 1
        
        r = 0
        # find all the campaign organizer and append it to df_donation
        for don in soup.find_all("span", {"class": div_class_projectname}):
            don = don.text
            df_projects.loc[r, 'project_name'] = don
            r = r + 1
        
        r = 0
        # find all the campaign total donation and append it to df_donation
        for don in soup.find_all("div", {"class": div_class_donationreceived}):
            don = don.text
            don = don.replace('TerkumpulRp', '')
            don = don.replace('TersediaRp', '')
            don = don.replace('.', '')
            df_projects.loc[r, 'donation_received'] = don
            r = r + 1
        
        r = 0    
        # find all the campaign days remaining and append it to df_donation
        for don in soup.find_all("div", {"class": div_class_daystogo}):
            don = don.text
            don = don.replace('Sisa hari', '')
            df_projects.loc[r, 'days_to_go'] = don
            r = r + 1
        
        df_projects['time_scraped'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        today = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.today = today
        
        filepath = Path(self.save_path + 'project_list_' + today + '.csv')  
        filepath.parent.mkdir(parents=True, exist_ok=True)  
        
        # prepare the project_list for the projectprops_scrape() method
        self.project_list = df_projects['short_url'] 
        df_projects.to_csv(filepath, index=False)
        
        return df_projects
    

    def projectprops_scrape(self):
        '''
        Scrape all information about the projects from a list of projects we got from the homepage.
        
        Args:
        - donation_list (list): List of donation IDs to scrape.
        - flpath (str): Path to save the scraped data.
        
        Returns:
        - pd.DataFrame: DataFrame containing the scraped data.
        '''

        df_project_props = pd.DataFrame()

        project_list = self.project_list
        
        for project_id in project_list:
            try:
                url = 'view-source:https://kitabisa.com/campaign/' + project_id
            
                self.driver_projectprops.get(url)
                content = self.driver_projectprops.page_source

                # only parse the json file from the html, the hidden script
                # start and the end is the html structure from kitabisa to take only the JSON part, adjust based on the dynamics of the changes
                start = '__NEXT_DATA__</span>" <span class="html-attribute-name">type</span>="<span class="html-attribute-value">application/json</span>"&gt;</span>'
                end = '<span class="html-tag">&lt;/script&gt;</span><span class="html-tag">'

                json_script = content.split(start)[1].split(end)[0]
                #print(json_script)
        
                json_format = json.loads(json_script)

                # BEWARE: json_format hierarchical structure might change over time, always check
                df = pd.json_normalize(json_format['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['dataCampaigns'])
                df['time_scraped'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                df_project_props = pd.concat([df_project_props, df], ignore_index=True)
                
                # debuggers to see which projects we already read
                with open(f'{self.save_path}log_projectprops.txt', 'a') as fh:
                    print('succesfully read ' + str(project_id), file=fh)
            
            except:
                # debuggers to see which files went to error
                with open(f'{self.save_path}log_projectprops.txt', 'a') as fh:
                    print('error when reading ' + str(project_id), file=fh)
                    pass
                
        filepath = Path(self.save_path + 'project_props_' + self.today + '.csv')
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df_project_props.to_csv(filepath, index=False)
        
        return df_project_props, filepath
    

def projects_data_cleaning(file_path, cols_to_take, save_path):

    df_project_props = pd.read_csv(file_path)
    df_project_props = df_project_props[cols_to_take].copy(deep=True)

    # calculate days passed since the campaign started
    current_timestamp = int(time.time())
    df_project_props['days_passed'] = (current_timestamp - df_project_props['campaign_start']) / (24 * 60 * 60)
    df_project_props['days_passed'] = df_project_props['days_passed'].map(math.ceil)

    # convert it to a datetime format instead of unix
    df_project_props['campaign_start'] = df_project_props['campaign_start'].apply(lambda x: datetime.fromtimestamp(x))
    df_project_props['campaign_end'] = df_project_props['campaign_end'].apply(lambda x: datetime.fromtimestamp(x))

    # take the timestamp part of the filename, as it will be used to name our file
    file_name = os.path.basename(file_path)
    timestamp_part = file_name.split('_')[-1].replace('.csv', '')  

    filepath = Path(save_path + 'project_cleaned' + timestamp_part + '.csv')
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df_project_props.to_csv(filepath, index=False)


class ProjectsFinalize:
    '''
    A class for finalizing project data by cleaning and filtering.

    Parameters:
    - file_path (str): The path to the CSV file containing project data.
    - save_path (str): The path to save the cleaned and filtered CSV files.
    '''

    def __init__(self, file_path, save_path):
        self.file_path = file_path
        self.save_path = save_path


    def projects_data_cleaning(self, cols_to_take):
        '''
        Clean the project data and save it to a CSV file.

        Parameters:
        - cols_to_take (list): A list of column names to keep in the cleaned data.
        '''
        df_projects_cleaned = pd.read_csv(self.file_path)
        df_projects_cleaned = df_projects_cleaned[cols_to_take].copy(deep=True)

        # calculate days passed since the campaign started
        current_timestamp = int(time.time())
        df_projects_cleaned['days_passed'] = (current_timestamp - df_projects_cleaned['campaign_start']) / (24 * 60 * 60)
        df_projects_cleaned['days_passed'] = df_projects_cleaned['days_passed'].map(math.ceil)

        # convert it to a datetime format instead of unix
        df_projects_cleaned['campaign_start'] = df_projects_cleaned['campaign_start'].apply(lambda x: datetime.fromtimestamp(x))
        df_projects_cleaned['campaign_end'] = df_projects_cleaned['campaign_end'].apply(lambda x: datetime.fromtimestamp(x))

        # take the timestamp part of the filename, as it will be used to name our file
        file_name = os.path.basename(self.file_path)
        timestamp_part = file_name.split('_')[-1].replace('.csv', '')  

        # save the dataframe to local, for cache
        filepath = Path(self.save_path + 'project_cleaned_' + timestamp_part + '.csv')
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df_projects_cleaned.to_csv(filepath, index=False)
        
        # container for the variables we'd use again later
        self.timestamp_part = timestamp_part
        self.projects_cleaned_path = filepath


    def projects_filter(self, donation_pct, dev_mode=False):
        '''
        Filter the project data based on donation percentage and other criteria.

        Parameters:
        - donation_pct (float): The minimum (or maximum, depending on dev_mode) donation percentage to include a project.
        - dev_mode (bool, optional): If True, projects with a donation percentage greater than the provided donation_pct will be included.
                                     If False, projects with a donation percentage less than the provided donation_pct will be included.
                                     Defaults to False.


        Returns:
        - df_projects_final (DataFrame): The final filtered DataFrame of projects.
        '''
        df_projects_final = pd.read_csv(self.projects_cleaned_path)

        # criteria list for projects that we want to analyze
        df_projects_final = df_projects_final[df_projects_final['is_forever_running'] == False]
        df_projects_final = df_projects_final[df_projects_final['is_open_goal'] == False]
        
        if dev_mode == True:
            df_projects_final = df_projects_final[(df_projects_final['donation_percentage'] > 0.1) &            # more than 10%, to avoid projects who're just initiated
                                                  (df_projects_final['donation_percentage'] < donation_pct)]    # less than donation_pct for the dev_mode
        elif dev_mode == False:
            df_projects_final = df_projects_final[df_projects_final['donation_percentage'] > donation_pct]
        else:
            raise ValueError("dev_mode should be boolean value.")

        # save the final dataframe of our projects list
        filepath = Path(self.save_path + 'project_final_' + self.timestamp_part + '.csv')
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df_projects_final.to_csv(filepath, index=False)

        return df_projects_final, filepath


if __name__ == '__main__':
    url = 'https://kitabisa.com/explore/all'
    save_path = 'data/'
    num_scroll = 3
    
    # scrape the data first
    with Scraper(save_path) as scraper:
        df_projects = scraper.projectlist_scrape(url, num_scroll)
        df_project_props, file_path = scraper.projectprops_scrape()

    # do the data cleaning and filtering to get the final dataframe
    cols_to_take = ['short_url', 'donation_count', 'donation_received', 'donation_target', 'donation_percentage', 
                    'campaign_start', 'campaign_end', 'days_remaining', 'category.name', 'is_forever_running', 'is_open_goal']

    df_projects_final = ProjectsFinalize(file_path, save_path)
    df_projects_final.projects_data_cleaning(cols_to_take)

    df_projects_final = df_projects_final.projects_filter(donation_pct=0.3, dev_mode=True)
    
    print("Successfully scrape the data to a CSV file.")