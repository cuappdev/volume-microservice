import json
import os
from article import Article
from publication import Publication
from pymongo import MongoClient, UpdateOne

with open("publications.json") as f:
    publications_json = json.load(f)["publications"]

publications = []
articles = []
for publication in publications_json:
    pub = Publication(publication)
    for entry in pub.get_feed():
        articles.append(Article(entry, publication['slug']).serialize())
    publications.append(pub.serialize())

publication_upserts = [ UpdateOne({'_id':p['_id']}, {'$setOnInsert':p}, upsert=True) for p in publications ]
article_upserts = [ UpdateOne({'articleUrl':a['articleUrl']}, {'$setOnInsert':a}, upsert=True) for a in articles ]

MONGO_ADDRESS = os.getenv("MONGO_ADDRESS")
client = MongoClient(MONGO_ADDRESS)

db = client.microphone
result_pub = db.publications.bulk_write(publication_upserts)
result_art = db.articles.bulk_write(article_upserts)