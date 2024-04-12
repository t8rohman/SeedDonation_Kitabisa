from dagster import Definitions, load_assets_from_modules

from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_modules,
)

from . import assets


all_assets = load_assets_from_modules([assets])

kitabisascrape_job = define_asset_job('kitabisascrape_job', 
                                      selection=AssetSelection.all()
                                      )

kitabisascrape_schedule = ScheduleDefinition(job=kitabisascrape_job,        # pass the kitabisa scrape job to the scheduler
                                             cron_schedule='0 19 * * *'     # schedule by following cron scheduler format
                                             )

# dagster `Definitions()`` are entities that dagster learns about by importing your code
# we use Definitions() object here to combine definitions and have them aware of each other
# combine between assets, jobs, and the schedule

defs = Definitions(
    assets=all_assets,                      # pass all assets, as we want to use all assets from the module
    jobs=[kitabisascrape_job],              # pass the job...
    schedules=[kitabisascrape_schedule]     # and the scheduler
)