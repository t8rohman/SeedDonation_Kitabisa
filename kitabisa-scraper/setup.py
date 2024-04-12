from setuptools import find_packages, setup

setup(
    name="kitabisa_scraper",
    packages=find_packages(exclude=["kitabisa_scraper_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "beautifulsoup4==4.11.1",
        "pandas==1.5.3",
        "selenium==4.19.0"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
