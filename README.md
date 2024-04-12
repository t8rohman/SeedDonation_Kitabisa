# Will Seed Money Work in a Real Life Setting?

> Securing Donations in Fundraising Sites: The Use of Seed Money for Campaigns

Numerous studies have researched the impact of seed money on charitable giving, mostly concluding that it boosts donations. This study aims to bridge academic findings to practical application by investigating if adding seed money to a fundraising campaign increases visitor donations. The research focuses on observing donation behavior on the crowdfunding site Kitabisa, analyzing how campaign progress influences donation size and willingness to donate. To achieve this, it's crucial to have information on the donations made over time and their respective sizes.

The repository showcases an end-to-end data pipeline developed with Dagster. It extracts data from Kitabisa on campaigns and donations, provides a Jupyter notebook for data analysis, and presents results in a PDF format.

## Data Extraction

The data extraction phase is divided into two parts: **extracting projects** and **extracting donation** information.

### Extracting Projects

First, we extract the project list from the homepage along with brief information for filtering purposes. We use the `Scraper` class from the `projects` module for this task. Here's the code:

```python
from projects import Scraper

url = 'https://kitabisa.com/explore/all'
save_path = 'data/'
num_scroll = 300

with Scraper(save_path) as scraper:
  df_projects = scraper.projectlist_scrape(url, num_scroll)
  df_project_props, file_path = scraper.projectprops_scrape()
```

Next, we clean the data using the `ProjectsFinalize` class from the `projects` module. We can specify a minimum donation percentage for filtering. Here, we set it to 90% to focus on projects with high donation progress:

```python
from projects import ProjectsFinalize

cols_to_take = ['short_url', 'donation_count', 'donation_received', 'donation_target', 'donation_percentage',
                'campaign_start', 'campaign_end', 'days_remaining', 'category.name', 'is_forever_running', 'is_open_goal']

df_projects_final = ProjectsFinalize(file_path, save_path)
df_projects_final.projects_data_cleaning(cols_to_take)

df_projects_final = df_projects_final.projects_filter(donation_pct=0.9)
```

### Extracting Donation Information

The list of projects meeting our donation percentage criteria is saved in the specified `save_path`. From this list, we can extract all donor information using the `Scraper` class from the `donors` module. Assuming we have the list of projects we want to extract in `list_projects_to_read`, we can call the class as follows:

```python
from donors import Scraper

save_path = 'data/'
max_attempts = 3

with Scraper(save_path) as scraper:
  for project in list_projects_to_read:
    scraper.donors_scrape(project, max_attempts)
```

Extracting all donor information may take some time, especially for projects with over 10,000 donations. Kitabisa's data structure splits donation information into pages of 10 donations each, requiring us to navigate through potentially thousands of pages. To handle errors during extraction, we can use the following class to resume scraping:

```python
from donors import Scraper

project_id = ...       # PUT PROJECT ID HERE, CAN BE TAKEN FROM THE URL OF THE PROJECT
start_id = ...         # THE ID OF THE PAGE WHEN WE ENCOUNTERED THE FAILURE, CAN BE CHECKED FROM THE DEBUG FILE
init = False           # SET THIS AS FALSE TO SHOW THAT WE'RE NOT GOING FROM THE BEGINNING

with Scraper(save_path) as scraper:
  scraper.donors_scrape(project_id, max_attempts, start_id, init=False)
```

## Orchestrating Data Pipeline

This repository also includes a data pipeline for daily data extraction using **Dagster**. The process is similar to manual extraction but runs automatically. You can find it in the `kitabisa_scraper` folder. This automated process is useful if you don't want to trigger the program manually every time.

A crucial point in bridging projects and donation information extraction is the projects_to_read asset in the Dagster pipeline. This asset automatically reads projects that haven't been extracted on the previous day. This feature is helpful if you schedule the data pipeline daily, set the minimum donation percentage at 90%, and plan to extract data over a long period, like a month or two.

For example, let's say on the first day, project A hasn't reached 90% donation progress, so it's filtered out. However, by the end of the extraction period, it surpasses that threshold. The code below allows us to automatically read the donation information for projects we haven't extracted:

```python
from dagster import AssetExecutionContext, MaterializeResult

@asset(deps=[projects_filter])
def projects_to_read(context: AssetExecutionContext) -> MaterializeResult:

    data_folder = 'data/'
    file_prefix = 'donorsinfo_appended_'
    file_suffix = '.csv'

    files = os.listdir(data_folder)
    filtered_files = [f for f in files if f.startswith(file_prefix) and f.endswith(file_suffix)]
    
    file_ids = [f.replace(file_prefix, '').replace(file_suffix, '') for f in filtered_files]
    projects_to_read = list(pd.read_csv(file_path)['short_url'])

    projects_to_read = [x for x in projects_to_read if x not in file_ids]

    return MaterializeResult(
        metadata={
            "projects_to_read": projects_to_read
        }
    )
```

You can also change the scheduling of the Dagster pipeline by modifying the `cron_schedule` in the `kitabisa_scraper/__init__.py` file:

```python
from dagster import ScheduleDefinition

kitabisascrape_schedule = ScheduleDefinition(job=kitabisascrape_job,       
                                             cron_schedule='0 19 * * *' 
                                             )
```

Nevertheless, If you plan to make changes to the Dagster pipeline, it's advisable to go through the tutorial and understand how Dagster works to avoid errors.

## Data Analysis

As mentioned earlier, this study aims to determine the effectiveness of seed donations in increasing people's donations. 

To achieve this, the study observes the number of people donating and the amount of donations as campaigns progress on the crowdfunding site Kitabisa. The goal is to understand how people's willingness to donate and their donation amounts are affected by a campaign's progress toward its goal.

You can find the analysis process and results under the `analysis` folder. It includes Jupyter notebook files and PDF presentation for a comprehensive understanding of the results.
