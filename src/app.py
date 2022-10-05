from decimal import InvalidOperation
import json
import logging
import os
import requests
import schedule
import re
import time
import gspread
from article import Article
from magazine import Magazine
from constants import STATES_LOCATION, GOOGLE_SHEET_ID
from publication import Publication
from pymongo import MongoClient, UpdateOne, errors


with open("publications.json") as f:
    publications_json = json.load(f)["publications"]
    publications = [Publication(p) for p in publications_json]

MONGO_ADDRESS = os.getenv("MONGO_ADDRESS")
DATABASE = os.getenv("DATABASE")
VOLUME_NOTIFICATIONS_ENDPOINT = os.getenv("VOLUME_NOTIFICATIONS_ENDPOINT")
GOOGLE_SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH")

# Auth into Google Service Account
gc = gspread.service_account(filename=GOOGLE_SERVICE_ACCOUNT_PATH)
sheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1


# Get serialized publications
publications_serialized = [p.serialize() for p in publications]
publication_upserts = [
    UpdateOne({"slug": p["slug"]}, {"$set": p}, upsert=True)
    for p in publications_serialized
]
# Add publications to db
with MongoClient(MONGO_ADDRESS) as client:
    db = client[DATABASE]
    result = db.publications.bulk_write(publication_upserts)

# Function for gathering articles for running with scheduler
def gather_articles():
    logging.info("Gathering articles")
    articles = []
    for p in publications:
        for entry in p.get_feed():
            articles.append(Article(entry, p).serialize())

    article_upserts = [
        UpdateOne({"articleURL": a["articleURL"]}, {"$set": a}, upsert=True)
        for a in articles
    ]
    # Add articles to db
    with MongoClient(MONGO_ADDRESS) as client:
        db = client[DATABASE]
        result = db.articles.bulk_write(article_upserts, ordered=False).upserted_ids
        # Need to unwrap ObjectID objects from MongoDB into str ids
        article_ids = [str(article) for article in result.values()]
        try:
            logging.info(f"Sending notification for {len(article_ids)} articles")
        #    requests.post(
        #         VOLUME_NOTIFICATIONS_ENDPOINT, data={"articleIDs": article_ids}
        #     )
        except:
            logging.error("Unable to connect to volume-backend.")


# Function for gathering magazines for running with scheduler
def gather_magazines():
    logging.info("Gathering magazines")
    magazines = []
    with MongoClient(MONGO_ADDRESS) as client:
        db = client[DATABASE]
        data = sheet.get_all_values()
        len_data = len(data)
        parse_counter = 1
        for i in range(1, len_data):
            if data[i][5] != "1" and data[i][0] != "":
                p = list(
                    filter(lambda p: p["slug"] == data[i][1], publications_serialized)
                )
                p = p[0] if p else None
                magazines.append(Magazine(data[i], p).serialize())
                sheet.update_cell(i + 1, 6, 1)
            else:
                parse_counter += 1
        if parse_counter < len_data:
            magazine_upserts = [
                UpdateOne({"pdfURL": m["pdfURL"]}, {"$set": m}, upsert=True)
                for m in magazines
            ]
            # Add magazines to db
            result = db.magazines.bulk_write(
                magazine_upserts, ordered=False
            ).upserted_ids

            # Need to unwrap ObjectID objects from MongoDB into str ids
            magazine_ids = [str(magazine) for magazine in result.values()]
            try:
                logging.info(f"Sending notification for {len(magazine_ids)} magazines")
            #    requests.post(
            #         VOLUME_NOTIFICATIONS_ENDPOINT, data={"magazineIDs": magazine_ids}
            #     )
            except:
                logging.error("Unable to connect to volume-backend.")


# Before first run, clear states
for f in os.listdir(STATES_LOCATION):
    os.remove(os.path.join(STATES_LOCATION, f))

# Get initial refresh
gather_magazines()
gather_articles()


# Schedule the function to run every 10 minutes
schedule.every(10).minutes.do(gather_articles)
schedule.every(10).minutes.do(gather_magazines)
while True:
    schedule.run_pending()
    time.sleep(60)
