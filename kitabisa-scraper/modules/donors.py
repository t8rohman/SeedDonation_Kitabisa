import pandas as pd
import json
import copy
from pathlib import Path  
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class Scraper:
    '''
    Class to scrape donor information from Kitabisa using Selenium WebDriver.
    
    Args:
        save_path (str): Path to save the scraped data.
    '''

    def __init__(self, save_path):
        self.save_path = save_path
        self.driver = None


    def __enter__(self):
        '''
        Enter method to initialize the Selenium WebDriver when used in a 'with' statement.
        '''
        # driver for projects information -> use headless to fasten the scraping process
        chrome_options = Options()
        # hide the chrome ui when running the webdriver
        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--window-size=1920,1080")
        # user agent to avoid the web incorrectly read the user agent as a headless browser
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36' 
        chrome_options.add_argument(f'user-agent={user_agent}')
        self.driver = webdriver.Chrome(options=chrome_options)

        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        '''
        Exit method to close the Selenium WebDriver when exiting the 'with' statement.
        '''
        self.driver.quit()


    def donors_scrape(self, project_id, max_attempts, start_id=None, init=True):
        '''
        Function to scrape list of all donors from a donation.
        
        Args:
            project_id (str): The short name of the project, taken from the URL.
            max_attempts (int): Define how many times we want to try before stopping the scraper.
            start_id (str, optional): The starting page ID for scraping. Defaults to None.
            init (bool, optional): Whether to initialize the scraper from the beginning of the donors information page. Defaults to True.
        '''
        save_path = self.save_path

        if not init and start_id is None:
            raise ValueError("If init is False, start_id must be provided.")

        # filepath_num for the iteration
        # next to append next page, filled an initial value to not trigger the while loop
        filepath_num = 0
        url = 'view-source:https://core.kitabisa.com/campaigns/' + project_id + '/donors?sort=verified&'  
        url_new = url

        # these will be used only if you set the init as False
        if init == False:
            url_start = url + 'next=' + start_id
            url_cont = url
            i = 0

        # placeholder for current_page_id and next_page_id
        df_appended = pd.DataFrame()
        next_page_id = 'page_1' 
        current_page_id = 'page_1'
    
        attempt = 0

        while next_page_id != '' and attempt < max_attempts:
            try:
                if init == True:
                    self.driver.get(url_new)
                else:
                    if i == 0:
                        self.driver.get(url_start)
                    else:
                        self.driver.get(url_cont)
                
                content = self.driver.page_source
                content = self.driver.find_element(By.CLASS_NAME, ('line-content')).text

                data = json.loads(content)  # this is the json data for the list of the donors
            
                df = pd.json_normalize(data, record_path=['data'])
                df['time_scrapped']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                df['short_url'] = project_id
                df_appended = pd.concat([df_appended, df], ignore_index=True)

                filepath_num = filepath_num + 1
                filepath = Path(save_path + 'donorsinfo_individual_' + project_id + '/' + str(filepath_num) +'.csv')  
                filepath.parent.mkdir(parents=True, exist_ok=True)  
                df.to_csv(filepath, index=False)
                
                # create a current_page_id first, which is the value of current page for debugging purpose
                # then, we can update the the next_page_id with the new id
                current_page_id = copy.deepcopy(next_page_id)
                next_page_id = data['next']
                url_new = url + 'next=' + next_page_id

                if init == False:
                    url_cont = url + 'next=' + next_page_id
                    i += 1
                
                # debuggers to see which files we already read
                with open(f'{save_path}donorsinfo_individual_{project_id}/log_donorsinfo.txt', 'a') as fh:
                    print('succesfully read ' + project_id + ' at the page of ' + current_page_id, file=fh)

                # reset attempt counter if we successfully read the donors info at that page
                attempt = 0
                
            except:
                attempt += 1
                # debuggers to see which files went to error
                with open(f'{save_path}donorsinfo_individual_{project_id}/log_donorsinfo.txt', 'a') as fh:
                    print(f'Attempt {attempt}: error when reading {project_id} at the page of {current_page_id}', file=fh)
                pass
                
        filepath = Path(save_path + 'donorsinfo_appended_' + project_id + '.csv')  
        filepath.parent.mkdir(parents=True, exist_ok=True)  
        df_appended.to_csv(filepath, index=False)


if __name__ == '__main__':
    # only for testing purpose, change the project_id accordingly
    project_id = 'sehatisyawaljumatbaik'
    save_path = 'data/'
    max_attempts = 3

    with Scraper(save_path) as scraper:
        scraper.donors_scrape(project_id, max_attempts)
    
    print('Sucessfully read all the donors information.')