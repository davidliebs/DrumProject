import b2sdk.v2 as b2
import os
from dotenv import load_dotenv

load_dotenv()

def returnBucket():
	info = b2.InMemoryAccountInfo()
	b2_api = b2.B2Api(info)

	b2_api.authorize_account("production", os.getenv("backblaze_bucket_key_id"), os.getenv("backblaze_bucket_key"))
	bucket = b2_api.get_bucket_by_name(os.getenv("bucket_name"))

	return b2_api, bucket

def uploadFileToBucket(b2_api, bucket, filepath, filename):
	uploaded_file = bucket.upload_local_file(
		local_file=filepath,
		file_name="challenges/"+filename
	)

	return b2_api.get_download_url_for_fileid(uploaded_file.id_)