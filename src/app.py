import gspread
import json
import logging
import os
import requests
import schedule
import time

from article import Article
from constants import DEV_FLYER_SHEET_ID, DEV_GOOGLE_SHEET_ID, PROD_FLYER_SHEET_ID, PROD_GOOGLE_SHEET_ID, STATES_LOCATION
from flyer import Flyer
from magazine import Magazine
from organization import Organization
from publication import Publication
from pymongo import MongoClient, UpdateOne




# set base config of logger to log timestamps and info level
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

with open("publications.json") as f:
    publications_json = json.load(f)["publications"]
    publications = [Publication(p) for p in publications_json]

with open("organizations.json") as f:
    organizations_json = json.load(f)["organizations"]
    organizations = [Organization(o) for o in organizations_json]

MONGO_ADDRESS = os.getenv("MONGO_ADDRESS")
DATABASE = os.getenv("DATABASE")
VOLUME_NOTIFICATIONS_ENDPOINT = os.getenv("VOLUME_NOTIFICATIONS_ENDPOINT")
GOOGLE_SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH")
SERVER = os.getenv("SERVER")

if SERVER == "prod":
    google_sheet_id = PROD_GOOGLE_SHEET_ID
    flyer_sheet_id = PROD_FLYER_SHEET_ID
else:
    google_sheet_id = DEV_GOOGLE_SHEET_ID
    flyer_sheet_id = DEV_FLYER_SHEET_ID
# Auth into Google Service Account
gc = gspread.service_account(filename=GOOGLE_SERVICE_ACCOUNT_PATH)
sheet = gc.open_by_key(google_sheet_id).sheet1
flyer_sheet = gc.open_by_key(flyer_sheet_id).sheet1


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

# Get serialized organizations
organizations_serialized = [o.serialize() for o in organizations]
organization_upserts = [
    UpdateOne({"slug": o["slug"]}, {"$set": o}, upsert=True)
    for o in organizations_serialized
]
# Add organizations to db
with MongoClient(MONGO_ADDRESS) as client:
    db = client[DATABASE]
    result = db.organizations.bulk_write(organization_upserts)

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
        if article_ids:
            try:
                logging.info(f"Sending notification for {len(article_ids)} articles")
                requests.post(
                    VOLUME_NOTIFICATIONS_ENDPOINT + "/articles/",
                    json={"articleIDs": article_ids},
                )
            except Exception as e:
                logging.error("Articles unable to connect to volume-backend.")
                print(e)
    logging.info("Done gathering articles\n")


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
            parsed = data[i][7] == "1"
            data_is_empty = data[i][0] == ""
            if not parsed and not data_is_empty:
                slug = data[i][2]
                p = list(filter(lambda p: p["slug"] == slug, publications_serialized))
                p = p[0] if p else None  # Get only one publication
                magazines.append(Magazine(data[i], p).serialize())
                sheet.update_cell(i + 1, 8, 1)  # Updates parsed to equal 1
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

                requests.post(
                    VOLUME_NOTIFICATIONS_ENDPOINT + "/magazines/",
                    json={"magazineIDs": magazine_ids},
                )
            except Exception as e:
                logging.error("Magazines unable to connect to volume-backend.")
                print(e)
    logging.info("Done gathering magazines\n")

# Function for gathering magazines for running with scheduler
def gather_flyers():
    logging.info("Gathering flyers")
    flyers = []
    with MongoClient(MONGO_ADDRESS) as client:
        db = client[DATABASE]
        data = flyer_sheet.get_all_values()
        len_data = len(data)
        parse_counter = 1
        for i in range(1, len_data):
            parsed = data[i][11] == "1"
            data_is_empty = data[i][0] == ""
            if not parsed and not data_is_empty:
                slug = data[i][4]
                o = list(filter(lambda o: o["slug"] == slug, organizations_serialized))
                
                o = o[0] if o else None  # Get only one organization
                flyers.append(Flyer(data[i], o).serialize())
                flyer_sheet.update_cell(i + 1, 12, 1)  # Updates parsed to equal 1
            else:
                parse_counter += 1
        if parse_counter < len_data:
            flyer_upserts = [
                UpdateOne({"imageURL": f["imageURL"]}, {"$set": f}, upsert=True)
                for f in flyers
            ]
            # Add flyers to db
            db.flyers.bulk_write(flyer_upserts, ordered=False).upserted_ids

            
    logging.info("Done gathering flyers\n")


# Before first run, clear states
for f in os.listdir(STATES_LOCATION):
    os.remove(os.path.join(STATES_LOCATION, f))

# Get initial refresh
gather_magazines()
gather_articles()
gather_flyers()

# Schedule the function to run every 10 minutes
schedule.every(10).minutes.do(gather_articles)
schedule.every(10).minutes.do(gather_magazines)
schedule.every(10).minutes.do(gather_flyers)
while True:
    schedule.run_pending()
    time.sleep(60)
