import pandas as pd
import os
from modules import projects, donors
from dagster import asset, AssetKey, AssetExecutionContext, MetadataValue, MaterializeResult


@asset
def projects_scraper(context: AssetExecutionContext) -> MaterializeResult:
    url = 'https://kitabisa.com/explore/all'
    num_scroll = 300
    save_path = 'data/'

    with projects.Scraper(save_path) as projects_scraper:
        df_projects = projects_scraper.projectlist_scrape(url, num_scroll)
        df_project_props, file_path = projects_scraper.projectprops_scrape()
    
    context.log.info(f"Successfully scrape {len(df_projects)} projects the data to a CSV file.")
    
    return MaterializeResult(
        metadata={
            "num_records": len(df_projects), 
            "preview": MetadataValue.md(df_project_props.head().to_markdown()),
            "file_path": file_path  # pass file_path to downstream (projects_filter) function
        }
    )


@asset(deps=[projects_scraper])
def projects_filter(context: AssetExecutionContext) -> MaterializeResult:

    # access metadata that contains file_path from upstream function (projects_scraper)
    event_log_entry = context.instance.get_latest_materialization_event(AssetKey('projects_scraper'))     
    metadata = event_log_entry.dagster_event.event_specific_data.materialization.metadata     
    file_path = metadata['file_path'].value

    # define where to save the data
    save_path = 'data/'
    donation_pct = 0.5

    cols_to_take = ['short_url', 'donation_count', 'donation_received', 'donation_target', 'donation_percentage', 
                    'campaign_start', 'campaign_end', 'days_remaining', 'category.name', 'is_forever_running', 'is_open_goal']

    df_projects_final = projects.ProjectsFinalize(file_path, save_path)
    df_projects_final.projects_data_cleaning(cols_to_take)

    df_projects_final, file_path = df_projects_final.projects_filter(donation_pct, dev_mode=True)

    context.log.info(f"Successfully cleaned and produce the final dataframe! Total records: {len(df_projects_final)}.")

    return MaterializeResult(
        metadata={
            "num_records": len(df_projects_final), 
            "preview": MetadataValue.md(df_projects_final.head().to_markdown()),
            "filtered_file_path": file_path
        }
    )


@asset(deps=[projects_filter])
def projects_to_read(context: AssetExecutionContext) -> MaterializeResult:
    
    # access metadata that contains file_path from upstream function (projects_filter)
    event_log_entry = context.instance.get_latest_materialization_event(AssetKey('projects_filter'))     
    metadata = event_log_entry.dagster_event.event_specific_data.materialization.metadata     
    file_path = metadata['filtered_file_path'].value

    # filter all projects that we haven't read and saved into the data folder
    data_folder = 'data/'
    file_prefix = 'donorsinfo_appended_'
    file_suffix = '.csv'

    files = os.listdir(data_folder)
    filtered_files = [f for f in files if f.startswith(file_prefix) and f.endswith(file_suffix)]
    
    # file_ids, that includes all the projects we have read
    # projects_to_read, that includes all the projects we have filtered from the scraped data
    file_ids = [f.replace(file_prefix, '').replace(file_suffix, '') for f in filtered_files]
    projects_to_read = list(pd.read_csv(file_path)['short_url'])

    # filter out projects_to_read
    projects_to_read = [x for x in projects_to_read if x not in file_ids]

    return MaterializeResult(
        metadata={
            "projects_to_read": projects_to_read
        }
    )


@asset(deps=[projects_to_read])
def donors_scraper(context: AssetExecutionContext) -> None:
   
    # access metadata that contains file_path from upstream function (projects_scraper)
    event_log_entry = context.instance.get_latest_materialization_event(AssetKey('projects_to_read'))     
    metadata = event_log_entry.dagster_event.event_specific_data.materialization.metadata     
    list_projects_to_read = metadata['projects_to_read'].value

    save_path = 'data/'
    max_attempts = 3

    with donors.Scraper(save_path) as scraper:
        for project in list_projects_to_read:
            scraper.donors_scrape(project, max_attempts)
    
    context.log.info(f"Successfully read all the donor information from the projects we have.")