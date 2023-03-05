from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

def returnDBConnection():
	conn = mysql.connector.connect(
		user = os.getenv("db_user"),
		password = os.getenv("db_password"),
		database = os.getenv("db_database"),
		host = os.getenv("db_host"),
		port = int(os.getenv("db_port"))
	)
	cur = conn.cursor()

	return conn, cur

def authenticate_token(headers):
	if headers.get("Authorisation") == os.getenv("beatbuddy_api_key"):
		return True
	
	return False