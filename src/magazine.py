from __future__ import print_function
import base64
from better_profanity import profanity as pf
from constants import FILTERED_WORDS, UPLOAD_BUCKET
from dateutil import parser as date_parser
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import io
import json
import os
import requests
import pypdfium2 as pdfium


class Magazine:
    def __init__(self, sheet_row, publication):
        pf.load_censor_words(FILTERED_WORDS)
        self.timestamp = sheet_row[0]
        self.slug = sheet_row[2]
        self.title = sheet_row[3]
        self.drive_link = sheet_row[4]
        self.file_id = self.drive_link[self.drive_link.index("id=") + 3 :]
        self.date_pub = sheet_row[5]
        self.semester = sheet_row[6].lower()
        self.publication = publication

    def download_magazine(self, id):
        """
        pdf response and first image response from appdev upload service
        
        returns response tuple (<pdf_response>, <first_page_response>):
        ({"success": <bool>, "data": "<pdf url?>"}, {"success": <bool>, "data": "<first page png url?>"})
        """
        creds = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH"))
        
        try:
            # create drive api client
            service = build("drive", "v3", credentials=creds)

            # pylint: disable=maybe-no-member
            request = service.files().get_media(fileId=self.file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                
        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None
            
        if file is not None:
            pdf = pdfium.PdfDocument(file)
            first_page = pdf[0]
            pil_image = first_page.render().to_pil().resize((150,220))

            imageBytes = io.BytesIO() #create bytes stream to hold image
            pil_image.save(imageBytes, format='png')
            
            image_payload = json.dumps(
            {
            "bucket": "volume",
            "image": "data:image/png;base64,"
            + base64.b64encode(imageBytes.getvalue()).decode("utf-8")})
            
            image_response = requests.post("https://upload.cornellappdev.com/upload/",image_payload).text

            pdf_payload = json.dumps(
                {"bucket": UPLOAD_BUCKET,
                "image": "data:application/pdf;base64,"
                + base64.b64encode(file.getvalue()).decode("utf-8")})
            
            pdf_response  = requests.post("https://upload.cornellappdev.com/upload/",pdf_payload).text
            
            return (pdf_response, image_response)
        return None

    def get_date(self, date):
        return date_parser.parse(date)

    def serialize(self):
        pdf_response = self.download_magazine(id)[0]
        image_response = self.download_magazine(id)[1]
        
        image_response_obj = json.loads(image_response)
        if image_response_obj["success"]:
            image_url = image_response_obj["data"]
        else:
            raise Exception
        pdf_response_obj = json.loads(pdf_response)
        if pdf_response_obj["success"]:
            pdf_url = pdf_response_obj["data"]
            return {
                "date": self.get_date(self.timestamp),
                "published": self.date_pub,
                "semester": self.semester,
                "title": self.title,
                "publicationSlug": self.slug,
                "publication": self.publication,
                "pdfURL": pdf_url,
                "imageURL": image_url,
                "isFiltered": self.is_profane(),
            }
        else:
            raise Exception

    def is_profane(self):
        return pf.contains_profanity(self.title)
