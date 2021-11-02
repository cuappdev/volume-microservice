import json
import logging
import os
import requests
import schedule
import time
from article import Article
from publication import Publication
from pymongo import MongoClient, UpdateOne

with open("publications.json") as f:
    publications_json = json.load(f)["publications"]

MONGO_ADDRESS = os.getenv("MONGO_ADDRESS")
VOLUME_BACKEND_ADDRESS = os.getenv("VOLUME_BACKEND_ADDRESS")

# Get serialized publications
publications = [Publication(p).serialize() for p in publications_json]
publication_upserts = [
    UpdateOne({"_id": p["_id"]}, {"$setOnInsert": p}, upsert=True) for p in publications
]
# Add publications to db
with MongoClient(MONGO_ADDRESS) as client:
    db = client.volume
    result = db.publications.bulk_write(publication_upserts)

# Function for gathering articles for running with scheduler
def gather_articles():
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
        db = client.volume
        result = db.articles.bulk_write(article_upserts).upserted_ids
        article_ids = map(str, list(result.values()))
        response = requests.post(VOLUME_BACKEND_ADDRESS, data={'articleIDs': article_ids})

# Before first run, clear states
for f in os.listdir('./states/'):
    os.remove(os.path.join('./states/', f))

# Get initial refresh
gather_articles()

# Schedule the function to run every 1 hour
schedule.every().hour.do(gather_articles)
while True:
    schedule.run_pending()
    time.sleep(60)
