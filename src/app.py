import json
import os
import schedule
from article import Article
from publication import Publication
from pymongo import MongoClient, UpdateOne

# Open publications json file
with open("publications.json") as f:
    publications_json = json.load(f)["publications"]

MONGO_ADDRESS = os.getenv("MONGO_ADDRESS")

# Helper function to run multiple bulk write operations with one-time connection to database
def insert_to_db(op_arr):
    with MongoClient(MONGO_ADDRESS) as client:
        db = client.microphone
        result = db.publications.bulk_write(op_arr).bulk_api_result


publications = []
publication_upserts = [
    UpdateOne({"_id": p["_id"]}, {"$setOnInsert": p}, upsert=True) for p in publications
]
insert_to_db(publication_upserts)


def gather_articles():
    articles = []
    for publication in publications_json:
        pub = Publication(publication)
        for entry in pub.get_feed():
            articles.append(Article(entry, publication["slug"]).serialize())
        publications.append(pub.serialize())

    article_upserts = [
        UpdateOne({"articleUrl": a["articleUrl"]}, {"$setOnInsert": a}, upsert=True)
        for a in articles
    ]
    insert_to_db(article_upserts)


schedule.every(2).hour.do(gather_articles)
