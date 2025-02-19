#!/usr/bin/python3
#utility to run web scraper and manipulate database from command line.

import sys


if len(sys.argv) == 1:
    print(
"""
Avaliable args (can be combined):
--scrape: scrapes to database
--clear-database: remove everything from database
--add-placeholder: add placeholders to database
"""
            )

from database import Database
for command in sys.argv[1:]:
    match command:
        case "--scrape":
            print("scraping to database")
            database = Database()
            from web_scraper import add_all_to_database
            add_all_to_database(database)
            database.commitToDatabase()
            database.close()
        case "--clear-database":
            print("clearing database")
            database = Database()
            database.droppAllData()
            database.commitToDatabase()
            database.close()
        case "--add-placeholder":
            print("add placeholders to database")
            database = Database()
            database.fillDatabase()
            database.commitToDatabase()
            database.close()




