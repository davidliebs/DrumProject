import uuid
import mysql.connector
import process_challenge_files
import json
import pandas as pd
import shutil
import os
import blob_storage_library
import requests

b2_api, bucket = blob_storage_library.returnBucket()

class Course:
	def __init__(self, course_filepath, course_name, course_description, no_challenges):
		self.course_filepath = course_filepath
		self.df = pd.read_csv(os.path.join(self.course_filepath, "course.csv"))

		data = {"courseName": course_name, "courseDescription": course_description, "courseNoChallenges": no_challenges}
		
		res = requests.post(f"{os.getenv('api_base_url')}/creator/create_course_entry", json=data)
		self.course_id = res.text
	
	def uploadCourseLogo(self):
		params={"course_id": self.course_id}
		files=[
			('course_logo',('course-logo.png',open(os.path.join(self.course_filepath, "course-logo.png"),'rb'),'image/png'))
		]

		requests.post(f"{os.getenv('api_base_url')}/creator/upload_course_logo", params=params, files=files)

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

course = Course("/home/david/Desktop/BeatBuddy/Courses/Beginner Rock Course/", 
				"BeatBuddy Beginner Rock course", "Get started with beatbuddys very own beginner rock course!", 
				10
)

course.uploadCourseLogo()
course.populateChallengesTable()