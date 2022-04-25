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
from pymongo import MongoClient, UpdateOne
import gridfs


with open("publications.json") as f:
    publications_json = json.load(f)["publications"]
    # magazines_publications_json = json.load(f)["magazine_publications"]

MONGO_ADDRESS = os.getenv("MONGO_ADDRESS")
DATABASE = os.getenv("DATABASE")
VOLUME_NOTIFICATIONS_ENDPOINT = os.getenv("VOLUME_NOTIFICATIONS_ENDPOINT")
GOOGLE_SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH")
GOOGLE_SHEET_ID

# Auth into Google Service Account
gc = gspread.service_account(filename=GOOGLE_SERVICE_ACCOUNT_PATH)
sheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1


# Get serialized publications
publications = [Publication(p).serialize() for p in publications_json]
publication_upserts = [
    UpdateOne({"slug": p["slug"]}, {"$set": p}, upsert=True) for p in publications
]
# Add publications to db
with MongoClient(MONGO_ADDRESS) as client:
    db = client[DATABASE]
    result = db.publications.bulk_write(publication_upserts)

# Function for gathering articles for running with scheduler
def gather_articles():
    logging.info("Gathering articles")
    articles = []
    for publication in publications_json:
        p = Publication(publication)
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
    for publication in publications_json:
        p = Publication(publication)
        data = sheet.get_all_values()
        for i in range(len(data)):
            if i == 0:  # Header row in sheet
                continue
            if data[i][5] != "T":
                magazines.append(Magazine(data[i]).serialize())
                sheet.update_cell(i, 6, "T")

    # Add magazines to db
    with MongoClient(MONGO_ADDRESS) as client:
        db = client[DATABASE]
        result = db.magazines.bulk_write(magazines, ordered=False).upserted_ids
        # Need to unwrap ObjectID objects from MongoDB into str ids
        article_ids = [str(article) for article in result.values()]


# Before first run, clear states
for f in os.listdir(STATES_LOCATION):
    os.remove(os.path.join(STATES_LOCATION, f))

# Get initial refresh
gather_magazines()
gather_articles()


# Schedule the function to run every 1 hour
schedule.every(10).minutes.do(gather_articles)
while True:
    schedule.run_pending()
    time.sleep(60)
