import json
import logging
import os
import schedule
import time
from article import Article
from publication import Publication
from pymongo import MongoClient, UpdateOne

with open("publications.json") as f:
    publications_json = json.load(f)["publications"]

MONGO_ADDRESS = os.getenv("MONGO_ADDRESS")

# Get serialized publications
publications = [Publication(p).serialize() for p in publications_json]
publication_upserts = [
    UpdateOne({"_id": p["_id"]}, {"$setOnInsert": p}, upsert=True) for p in publications
]
# Add publications to db
with MongoClient(MONGO_ADDRESS) as client:
    db = client.microphone
    result = db.publications.bulk_write(publication_upserts)

# Function for gathering articles for running with scheduler
def gather_articles():
    articles = []
    for publication in publications_json:
        p = Publication(publication)
        for entry in p.get_feed():
            articles.append(Article(entry, publication["slug"]).serialize())

    article_upserts = [
        UpdateOne({"articleUrl": a["articleUrl"]}, {"$setOnInsert": a}, upsert=True)
        for a in articles
    ]
    # Add articles to db
    with MongoClient(MONGO_ADDRESS) as client:
        db = client.microphone
        result = db.articles.bulk_write(article_upserts)


# Get initial refresh
gather_articles()

# Schedule the function to run every 1 hour
schedule.every().hour.do(gather_articles)
while True:
    schedule.run_pending()
    time.sleep(60)
