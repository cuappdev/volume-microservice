import json
import logging
import os
import requests
import schedule
import time
from article import Article
from constants import STATES_LOCATION
from publication import Publication
from pymongo import MongoClient, UpdateOne

with open("publications.json") as f:
    publications_json = json.load(f)["publications"]

MONGO_ADDRESS = os.getenv("MONGO_ADDRESS")
DATABASE = os.getenv("DATABASE")
VOLUME_NOTIFICATIONS_ENDPOINT = os.getenv("VOLUME_NOTIFICATIONS_ENDPOINT")

# Get serialized publications
publications = [Publication(p).serialize() for p in publications_json]
publication_upserts = [
    UpdateOne({"slug": p["slug"]}, {"$setOnInsert": p}, upsert=True) for p in publications
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
            articles.append(Article(entry, publication["slug"]).serialize())

    article_upserts = [
        UpdateOne({"articleURL": a["articleURL"]}, {"$setOnInsert": a}, upsert=True)
        for a in articles
    ]
    # Add articles to db
    with MongoClient(MONGO_ADDRESS) as client:
        db = client[DATABASE]
        result = db.articles.bulk_write(article_upserts).upserted_ids
        # Need to unwrap ObjectID objects from MongoDB into str ids
        article_ids = [str(article) for article in result.values()]
        try:
            logging.info(f"Sending notification for {len(article_ids)} articles")
            # requests.post(VOLUME_NOTIFICATIONS_ENDPOINT, data={'articleIDs': article_ids})
        except:
            logging.error("Unable to connect to volume-backend.")

# Before first run, clear states
for f in os.listdir(STATES_LOCATION):
    os.remove(os.path.join(STATES_LOCATION, f))

# Get initial refresh
gather_articles()

# Schedule the function to run every 1 hour
schedule.every().hour.do(gather_articles)
while True:
    schedule.run_pending()
    time.sleep(60)
