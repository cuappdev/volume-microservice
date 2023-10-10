import gspread
import json
import logging
import os
import requests
import schedule
import time

from article import Article
from constants import (
    ACCESS_CODE_SHEET_ID,
    DEV_ORGANIZATION_SHEET_ID,
    DEV_GOOGLE_SHEET_ID,
    PROD_ORGANIZATION_SHEET_ID,
    PROD_GOOGLE_SHEET_ID,
    STATES_LOCATION,
)
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


MONGO_ADDRESS = os.getenv("MONGO_ADDRESS")
DATABASE = os.getenv("DATABASE")
VOLUME_NOTIFICATIONS_ENDPOINT = os.getenv("VOLUME_NOTIFICATIONS_ENDPOINT")
GOOGLE_SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH")
SERVER = os.getenv("SERVER")


# Auth into Google Service Account
gc = gspread.service_account(filename=GOOGLE_SERVICE_ACCOUNT_PATH)

if SERVER == "prod":
    google_sheet_id = PROD_GOOGLE_SHEET_ID
    org_sheet_id = PROD_ORGANIZATION_SHEET_ID
    access_code_sheet = gc.open_by_key(ACCESS_CODE_SHEET_ID).sheet2
else:
    google_sheet_id = DEV_GOOGLE_SHEET_ID
    org_sheet_id = DEV_ORGANIZATION_SHEET_ID
    access_code_sheet = gc.open_by_key(ACCESS_CODE_SHEET_ID).sheet1

sheet = gc.open_by_key(google_sheet_id).sheet1
org_sheet = gc.open_by_key(org_sheet_id).sheet1


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


# Function for gathering organizations for running with scheduler
def gather_orgs():
    logging.info("Gathering organizations")
    orgs = []
    with MongoClient(MONGO_ADDRESS) as client:
        db = client[DATABASE]
        data = org_sheet.get_all_values()
        len_data = len(data)
        parse_counter = 1
        parsed_column = 8
        for i in range(1, len_data):
            parsed = data[i][parsed_column] == "1"
            data_is_empty = data[i][0] == ""
            if not parsed and not data_is_empty:
                plainCode, org = Organization(data[i]).serialize()
                orgs.append(org)
                # Update parsed to equal 1
                org_sheet.update_cell(i + 1, parsed_column + 1, 1)
                # Update access code sheet
                access_code_sheet.append_row(
                    [org["slug"], plainCode, org["accessCode"]], table_range="A:D"
                )
            else:
                parse_counter += 1
        if parse_counter < len_data:
            org_upserts = [
                UpdateOne({"slug": org["slug"]}, {"$set": org}, upsert=True)
                for org in orgs
            ]
            # Add organizations to db
            db.organizations.bulk_write(org_upserts, ordered=False)

    logging.info("Done gathering organizations\n")


# Before first run, clear states
for f in os.listdir(STATES_LOCATION):
    os.remove(os.path.join(STATES_LOCATION, f))

# Get initial refresh
gather_magazines()
gather_articles()
gather_orgs()

# Schedule the function to run every 10 minutes
schedule.every(10).minutes.do(gather_articles)
schedule.every(10).minutes.do(gather_magazines)
schedule.every(10).minutes.do(gather_orgs)
while True:
    schedule.run_pending()
    time.sleep(60)
