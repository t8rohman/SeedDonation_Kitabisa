import scrape as sc


# function for scraping donation list

donation_list = sc.donationlist_scrapper("https://kitabisa.com/explore/all", 10)
print(len(donation_list))


# function to scrap donation information from all of donations in donation_list
# it's going to take a long time, depends on the length of the donation_list

i = 1
for donation in donation_list:
    print("Processing donation number " + str(i) + ".")
    sc.donor_scraper(donation, "/Users/mac/Documents/RU/THESIS/working_thesis/pilot_data_2/")
    i = i + 1


# function to scrap donation information from all of donations in donation_list
# it's going to take a long time, depends on the length of the donation_list

i = 1
for donation in donation_list:
    print("Processing donation number " + str(i) + ".")
    sc.donation_scraper(donation, "/Users/mac/Documents/RU/THESIS/working_thesis/pilot_data_2/")
    i = i + 1   



 
