import uuid
import mysql.connector
import process_challenge_files
import json
import pandas as pd
import shutil
import os
import blob_storage_library
import requests

conn = mysql.connector.connect(
	user = os.getenv("db_user"),
	password = os.getenv("db_password"),
	database = os.getenv("db_database"),
	host = os.getenv("db_host"),
	port = int(os.getenv("db_port"))
)
cur = conn.cursor()

b2_api, bucket = blob_storage_library.returnBucket()

class Course:
	def __init__(self, course_filepath, course_name, course_description, no_challenges):
		self.df = pd.read_csv(course_filepath)

		data = {"courseName": course_name, "courseDescription": course_description, "courseNoChallenges": no_challenges}
		
		res = requests.post(f"{os.getenv('api_base_url')}/creator/create_course_entry", json=data)
		self.course_id = res.text

	def populateChallengesTable(self):
		for index, row in self.df.iterrows():
			challenge_id = str(uuid.uuid4())
			music_data = json.dumps(process_challenge_files.return_formatted_midi_notes(row["midiFilepath"]))
			svg_indexes = json.dumps(process_challenge_files.return_svg_indexes(row["svgFilepath"]))

			fileURL = blob_storage_library.uploadFileToBucket(b2_api, bucket, row["svgFilepath"], challenge_id+".svg")

			data = {
				"challengeID": challenge_id,
				"courseID": self.course_id,
				"musicData": music_data,
				"svgIndexes": svg_indexes,
				"challengeNo": row["challengeNo"],
				"svgURL": fileURL,
				"challengeTitle": row["challengeTitle"],
				"challengeMessage": row["challengeMessage"]
			}

			res = requests.post(f"{os.getenv('api_base_url')}/creator/create_challenge_entry", json=data)

course = Course("/home/david/Desktop/BeatBuddy/Courses/Beginner Rock Course/course.csv", 
				"Rock course", "Get started with beatbuddys very own rock course!", 
				5
)
course.populateChallengesTable()

conn.close()