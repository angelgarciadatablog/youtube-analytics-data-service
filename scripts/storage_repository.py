import os
import json
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()


class StorageRepository:
    def __init__(self):
        bucket_name = os.getenv("GCS_BUCKET")
        if not bucket_name:
            raise ValueError("GCS_BUCKET no definido")
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def upload_dataframe_as_json(self, dataframe, filename, max_age=14400):
        json_data = dataframe.to_json(orient="records", date_format="iso", force_ascii=False)
        blob = self.bucket.blob(filename)
        blob.cache_control = f"public, max-age={max_age}"
        blob.upload_from_string(json_data, content_type="application/json")
        print(f"Subido: {filename}")
