# To run program:  python3 fth_api.py prashant

# README:  if conn error make sure password is set properly in RDS PASSWORD section

# README:  Debug Mode may need to be set to Fales when deploying live (although it seems to be working through Zappa)

import os
import uuid
import boto3
import json
import math

from datetime import time, date, datetime, timedelta
import calendar
import time
from pytz import timezone
import random
import string
import stripe

from flask import Flask, request, render_template
from flask_restful import Resource, Api
from flask_cors import CORS
from flask_mail import Mail, Message

# used for serializer email and error handling
# from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
# from flask_cors import CORS

from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.security import generate_password_hash, check_password_hash

#  NEED TO SOLVE THIS
# from NotificationHub import Notification
# from NotificationHub import NotificationHub

import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from twilio.rest import Client

from dateutil.relativedelta import *
from decimal import Decimal
from datetime import datetime, date, timedelta
from hashlib import sha512
from math import ceil
import string

# BING API KEY
# Import Bing API key into bing_api_key.py

#  NEED TO SOLVE THIS
# from env_keys import BING_API_KEY, RDS_PW

import decimal
import sys
import json
import pytz
import pymysql
import requests


s3 = boto3.client('s3')
s3_res = boto3.resource('s3')
s3_cl = boto3.client('s3')

# aws s3 bucket where the image is stored
# BUCKET_NAME = os.environ.get('MEAL_IMAGES_BUCKET')
# BUCKET_NAME = 'servingnow'
# allowed extensions for uploading a profile photo file
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

# RDS_HOST = 'pm-mysqldb.cxjnrciilyjq.us-west-1.rds.amazonaws.com'
RDS_HOST = 'io-mysqldb8.cxjnrciilyjq.us-west-1.rds.amazonaws.com'
# RDS_HOST = 'localhost'
RDS_PORT = 3306
# RDS_USER = 'root'
RDS_USER = 'admin'
RDS_DB = 'wwp'

# app = Flask(__name__)
app = Flask(__name__, template_folder='assets')

# --------------- Stripe Variables ------------------
# these key are using for testing. Customer should use their stripe account's keys instead
import stripe

stripe_public_key = 'pk_test_6RSoSd9tJgB2fN2hGkEDHCXp00MQdrK3Tw'

stripe_public_test_key = os.environ.get('stripe_public_test_key')
stripe_secret_test_key = os.environ.get('stripe_secret_test_key')

stripe_public_live_key = os.environ.get('stripe_public_live_key')
stripe_secret_live_key = os.environ.get('stripe_secret_live_key')

paypal_client_test_key = os.environ.get('paypal_client_test_key')
paypal_client_live_key = os.environ.get('paypal_client_live_key')

# Allow cross-origin resource sharing
cors = CORS(app, resources={r'/api/*': {'origins': '*'}})
app.config['DEBUG'] = True
# Adding for email testing
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_SERVER'] = 'smtp.mydomain.com'
app.config['MAIL_PORT'] = 465

app.config['MAIL_USERNAME'] = os.environ.get('SUPPORT_EMAIL')
app.config['MAIL_PASSWORD'] = os.environ.get('SUPPORT_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('SUPPORT_EMAIL')

app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Setting for gmail
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 465

app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Set this to false when deploying to live application
# app.config['DEBUG'] = True
app.config['DEBUG'] = False

mail = Mail(app)
# s = URLSafeTimedSerializer('thisisaverysecretkey')
# API
api = Api(app)

# convert to UTC time zone when testing in local time zone
utc = pytz.utc


def getToday(): return datetime.strftime(datetime.now(utc), "%Y-%m-%d")


def getNow(): return datetime.strftime(datetime.now(utc), "%Y-%m-%d %H:%M:%S")


# Get RDS password from command line argument
def RdsPw():
    if len(sys.argv) == 2:
        return str(sys.argv[1])
    return ""


# RDS PASSWORD
# When deploying to Zappa, set RDS_PW equal to the password as a string
# When pushing to GitHub, set RDS_PW equal to RdsPw()
RDS_PW = 'prashant'
# RDS_PW = RdsPw()


s3 = boto3.client('s3')

# aws s3 bucket where the image is stored
# BUCKET_NAME = os.environ.get('MEAL_IMAGES_BUCKET')
BUCKET_NAME = 'servingnow'
# allowed extensions for uploading a profile photo file
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

getToday = lambda: datetime.strftime(date.today(), "%Y-%m-%d")
getNow = lambda: datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")

# For Push notification
isDebug = False
NOTIFICATION_HUB_KEY = os.environ.get('NOTIFICATION_HUB_KEY')
NOTIFICATION_HUB_NAME = os.environ.get('NOTIFICATION_HUB_NAME')


# Connect to MySQL database (API v2)
def connect():
    global RDS_PW
    global RDS_HOST
    global RDS_PORT
    global RDS_USER
    global RDS_DB

    print("Trying to connect to RDS (API v2)...")
    try:
        conn = pymysql.connect(RDS_HOST,
                               user=RDS_USER,
                               port=RDS_PORT,
                               passwd=RDS_PW,
                               db=RDS_DB,
                               cursorclass=pymysql.cursors.DictCursor)
        print("Successfully connected to RDS. (API v2)")
        return conn
    except:
        print("Could not connect to RDS. (API v2)")
        raise Exception("RDS Connection failed. (API v2)")


# Disconnect from MySQL database (API v2)
def disconnect(conn):
    try:
        conn.close()
        print("Successfully disconnected from MySQL database. (API v2)")
    except:
        print("Could not properly disconnect from MySQL database. (API v2)")
        raise Exception("Failure disconnecting from MySQL database. (API v2)")


# Serialize JSON
def serializeResponse(response):
    try:
        print("In Serialize JSON")
        for row in response:
            for key in row:
                if type(row[key]) is Decimal:
                    row[key] = float(row[key])
                elif type(row[key]) is date:
                    row[key] = row[key].strftime("%Y-%m-%d")
                elif type(row[key]) is datetime:
                    row[key] = row[key].strftime("%Y-%m-%d %H:%M:%S")
        ##print("In Serialize JSON response", response)
        return response
    except:
        raise Exception("Bad query JSON")


# Execute an SQL command (API v2)
# Set cmd parameter to 'get' or 'post'
# Set conn parameter to connection object
# OPTIONAL: Set skipSerialization to True to skip default JSON response serialization
def execute(sql, cmd, conn, skipSerialization=False):
    response = {}
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            if cmd is 'get':
                result = cur.fetchall()
                response['message'] = 'Successfully executed SQL query.'
                # Return status code of 280 for successful GET request
                response['code'] = 280
                if not skipSerialization:
                    print('IN skipSerialization')
                    result = serializeResponse(result)
                response['result'] = result
            elif cmd in 'post':
                conn.commit()
                response['message'] = 'Successfully committed SQL command.'
                # Return status code of 281 for successful POST request
                response['code'] = 281
            else:
                response['message'] = 'Request failed. Unknown or ambiguous instruction given for MySQL command.'
                # Return status code of 480 for unknown HTTP method
                response['code'] = 480
    except:
        response['message'] = 'Request failed, could not execute MySQL command.'
        # Return status code of 490 for unsuccessful HTTP request
        response['code'] = 490
    finally:
        response['sql'] = sql
        return response


# Close RDS connection
def closeRdsConn(cur, conn):
    try:
        cur.close()
        conn.close()
        print("Successfully closed RDS connection.")
    except:
        print("Could not close RDS connection.")


# Runs a select query with the SQL query string and pymysql cursor as arguments
# Returns a list of Python tuples
def runSelectQuery(query, cur):
    try:
        cur.execute(query)
        queriedData = cur.fetchall()
        return queriedData
    except:
        raise Exception("Could not run select query and/or return data")


# ===========================================================
# Additional Helper Functions from sf_api.py
# Need to revisit to see if we need these

def helper_upload_user_img(file, key):
    bucket = 'wwp'
    if file and allowed_file(file.filename):
        filename = 'https://s3-us-west-1.amazonaws.com/' \
                   + str(bucket) + '/' + str(key)

        upload_file = s3.put_object(
            Bucket=bucket,
            Body=file,
            Key=key,
            ACL='public-read',
            ContentType='image/jpeg'
        )
        return filename
    return None


def helper_upload_refund_img(file, bucket, key):
    # print("Bucket = ", bucket)
    # print("Key = ", key)
    if file:
        filename = 'https://s3-us-west-1.amazonaws.com/' \
                   + str(bucket) + '/' + str(key)
        ##print('bucket:{}'.format(bucket))
        upload_file = s3.put_object(
            Bucket=bucket,
            Body=file,
            Key=key,
            ACL='public-read',
            ContentType='image/png'
        )
        return filename
    return None


def allowed_file(filename):
    """Checks if the file is allowed to upload"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# -- Stored Procedures start here -------------------------------------------------------------------------------


# RUN STORED PROCEDURES

def get_new_gameUID(conn):
    newGameQuery = execute("CALL captions.new_game_uid()", 'get', conn)
    if newGameQuery['code'] == 280:
        return newGameQuery['result'][0]['new_id']
    return "Could not generate new game UID", 500


def get_new_roundUID(conn):
    newRoundQuery = execute("CALL captions.new_round_uid()", 'get', conn)
    if newRoundQuery['code'] == 280:
        return newRoundQuery['result'][0]['new_id']
    return "Could not generate new game UID", 500


def get_new_userUID(conn):
    newUserQuery = execute("CALL wwp.new_user_uid()", 'get', conn)
    if newUserQuery['code'] == 280:
        return newUserQuery['result'][0]['new_id']
    return "Could not generate new user UID", 500


def get_new_historyUID(conn):
    newHistoryQuery = execute("CALL captions.new_history_uid()", 'get', conn)
    if newHistoryQuery['code'] == 280:
        return newHistoryQuery['result'][0]['new_id']
    return "Could not generate new history UID", 500


def get_new_paymentID(conn):
    newPaymentQuery = execute("CALL new_payment_uid", 'get', conn)
    if newPaymentQuery['code'] == 280:
        return newPaymentQuery['result'][0]['new_id']
    return "Could not generate new payment ID", 500


def get_new_contactUID(conn):
    newPurchaseQuery = execute("CALL io.new_contact_uid()", 'get', conn)
    if newPurchaseQuery['code'] == 280:
        return newPurchaseQuery['result'][0]['new_id']
    return "Could not generate new contact UID", 500


def get_new_appointmentUID(conn):
    newAppointmentQuery = execute("CALL io.new_appointment_uid()", 'get', conn)
    if newAppointmentQuery['code'] == 280:
        return newAppointmentQuery['result'][0]['new_id']
    return "Could not generate new appointment UID", 500


# --WWP Queries start here -------------------------------------------------------------------------------
class SignUp(Resource):
    def post(self):
        response = {}
        items = []
        try:
            conn = connect()
            data = request.get_json(force=True)
            print(data)
            role = data["role"]
            email = data["email"] if data.get("email") is not None else "NULL"
            phone = data["phone"] if data.get("phone") is not None else "NULL"
            timestamp = getNow()

            social_id = data["social_id"] if data.get("social_id") is not None else "NULL"
            # referral = data["referral_source"]

            # user_id = data["cust_id"] if data.get("cust_id") is not None else "NULL"

            if (
                    data.get("social") is None
                    or data.get("social") == "FALSE"
                    or data.get("social") == False
                    or data.get("social") == "NULL"
            ):
                social_signup = False
            else:
                social_signup = True

            print(social_signup)

            if social_signup == False:
                salt = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

                password = sha512((data["password"] + salt).encode()).hexdigest()
                print("password------", password)
                algorithm = "SHA512"
                mobile_access_token = "NULL"
                mobile_refresh_token = "NULL"
                user_access_token = "NULL"
                user_refresh_token = "NULL"
                user_social_signup = "NULL"
            else:
                mobile_access_token = data["mobile_access_token"]
                mobile_refresh_token = data["mobile_refresh_token"]
                user_access_token = data["user_access_token"]
                user_refresh_token = data["user_refresh_token"]
                salt = "NULL"
                password = "NULL"
                algorithm = "NULL"
                user_social_signup = data["social"]
                print("ELSE- OUT")

            # if cust_id != "NULL" and cust_id:
            #     NewUserID = cust_id
            #     query = (
            #             """
            #             SELECT user_access_token, user_refresh_token, mobile_access_token, mobile_refresh_token
            #             FROM io.customers
            #             WHERE customer_uid = \'""" + cust_id + """\';
            #         """
            #     )
            #     it = execute(query, "get", conn)
            #     print("it-------", it)
            #
            #     if it["result"][0]["user_access_token"] != "FALSE":
            #         user_access_token = it["result"][0]["user_access_token"]
            #
            #     if it["result"][0]["user_refresh_token"] != "FALSE":
            #         user_refresh_token = it["result"][0]["user_refresh_token"]
            #
            #     if it["result"][0]["mobile_access_token"] != "FALSE":
            #         mobile_access_token = it["result"][0]["mobile_access_token"]
            #
            #     if it["result"][0]["mobile_refresh_token"] != "FALSE":
            #         mobile_refresh_token = it["result"][0]["mobile_refresh_token"]
            #
            #     customer_insert_query = [
            #         """
            #             UPDATE io.customers
            #             SET
            #             customer_created_at = \'""" + (datetime.now()).strftime("%Y-%m-%d %H:%M:%S") + """\',
            #             customer_first_name = \'""" + firstName + """\',
            #             customer_last_name = \'""" + lastName + """\',
            #             customer_phone_num = \'""" + phone + """\',
            #             customer_address = \'""" + address + """\',
            #             customer_unit = \'""" + unit + """\',
            #             customer_city = \'""" + city + """\',
            #             customer_state = \'""" + state + """\',
            #             customer_zip = \'""" + zip_code + """\',
            #             customer_lat = \'""" + latitude + """\',
            #             customer_long = \'""" + longitude + """\',
            #             password_salt = \'""" + salt + """\',
            #             password_hashed = \'""" + password + """\',
            #             password_algorithm = \'""" + algorithm + """\',
            #             referral_source = \'""" + referral + """\',
            #             role = \'""" + role + """\',
            #             user_social_media = \'""" + user_social_signup + """\',
            #             social_timestamp  =  DATE_ADD(now() , INTERVAL 14 DAY)
            #             WHERE customer_uid = \'""" + cust_id + """\';
            #         """
            #     ]
            #
            # else:

            # check if there is a same customer_id existing
            check_user_query = """
                        SELECT user_uid FROM wwp.user
                        WHERE user_email = \'""" + email + """\'
                        OR user_phone = \'""" + phone + """\'
                        """

            user_info = execute(check_user_query, "get", conn)
            print("user_info: ", user_info)
            if user_info["code"] == 280:
                if user_info["result"]:
                    response["message"] = "User already exists, proceed to login."
                else:
                    print("Before write")
                    NewUserID = get_new_userUID()
                    print("New User ID: ", NewUserID)
                    # write everything to database
                    add_user_query = """
                        INSERT INTO wwp.user
                        SET user_uid = \'""" + NewUserID + """\',
                            user_timestamp = \'""" + timestamp + """\',
                            user_phone = \'""" + phone + """\',
                            user_email = \'""" + email + """\',
                            user_password_salt = \'""" + salt + """\',
                            user_password_algorithm = \'""" + algorithm + """\',
                            role = \'""" + role + """\',
                            user_social_media = \'""" + user_social_signup + """\',
                            user_access_token = \'""" + user_access_token + """\',
                            user_refresh_token = \'""" + user_refresh_token + """\',
                            mobile_access_token = \'""" + mobile_access_token + """\',
                            mobile_refresh_token = \'""" + mobile_refresh_token + """\',
                            user_social_media_id = \'""" + social_id + """\',
                            social_timestamp = \'""" + timestamp + """\'
                            """

            added_user = execute(add_user_query, "post", conn)
            print("add_user query info: ", added_user)
            if added_user["code"] == 281:
                response["message"] = "Signup successful"
                return response, 200

        except:
            print("Error happened while Sign Up")
            if "NewUserID" in locals():
                execute(
                    """DELETE FROM customers WHERE customer_uid = '"""
                    + NewUserID
                    + """';""",
                    "post",
                    conn,
                )
            raise BadRequest("Request failed, please try again later.")
        finally:
            disconnect(conn)


# -- Examples of Other Queries start here -------------------------------------------------------------------------------


# AVAILABLE APPOINTMENTS
class AvailableAppointments(Resource):
    def get(self, date_value):
        print("\nInside Available Appointments")
        response = {}
        items = {}

        try:
            conn = connect()
            print("Inside try block", date_value)

            # CALCULATE AVAILABLE TIME SLOTS
            query = """
                    -- FIND AVAILABLE TIME SLOTS - WORKS
                    SELECT -- *
                        DATE_FORMAT(ts_begin, '%T') AS start_time
                    FROM (
                        -- GET ALL TIME SLOTS
                        SELECT *,
                            TIME(ts.begin_datetime) AS ts_begin
                        FROM io.time_slots ts
                        -- LEFT JOIN WITH CURRENT APPOINTMENTS
                        LEFT JOIN (
                            SELECT * FROM io.appointments
                            WHERE appt_date = '""" + date_value + """') AS appt
                        ON TIME(ts.begin_datetime) = appt.appt_time
                        -- LEFT JOIN WITH AVAILABILITY
                        LEFT JOIN (
                            SELECT * FROM io.availability
                            WHERE date = '""" + date_value + """') AS avail
                        ON TIME(ts.begin_datetime) = avail.start_time_notavailable
                            OR (TIME(ts.begin_datetime) > avail.start_time_notavailable AND TIME(ts.end_datetime) <= ADDTIME(avail.end_time_notavailable,"0:29"))
                        -- LEFT JOIN WITH OPEN HOURS
                        LEFT JOIN (
                            SELECT * FROM nitya.days
                            WHERE dayofweek = DAYOFWEEK('""" + date_value + """')) AS openhrs
                        ON TIME(ts.begin_datetime) = openhrs.morning_start_time
                            OR (TIME(ts.begin_datetime) > openhrs.morning_start_time AND TIME(ts.end_datetime) <= ADDTIME(openhrs.morning_end_time,"0:29"))
                            OR TIME(ts.begin_datetime) = openhrs.afternoon_start_time
                            OR (TIME(ts.begin_datetime) > openhrs.afternoon_start_time AND TIME(ts.end_datetime) <= ADDTIME(openhrs.afternoon_end_time,"0:29"))
                    ) AS ts_avail
                    WHERE ISNULL(ts_avail.appointment_uid)   -- NO APPOINTMENTS SCHEDULED
                        AND ISNULL(ts_avail.prac_avail_uid)  -- NO AVAILABILITY RESTRICTIONS
                        AND !ISNULL(days_uid);               -- OPEN HRS ONLY
                    """

            available_times = execute(query, 'get', conn)
            print("Available Times: ", str(available_times['result']))
            print("Number of time slots: ", len(available_times['result']))
            # print("Available Times: ", str(available_times['result'][0]["start_time"]))

            return available_times

        except:
            raise BadRequest('Available Time Request failed, please try again later.')
        finally:
            disconnect(conn)


# BOOK APPOINTMENT
class CreateAppointment(Resource):
    def post(self):
        print("in Create Appointment class")
        response = {}
        items = {}
        try:
            conn = connect()
            data = request.get_json(force=True)
            print(data)
            # print to Received data to Terminal
            # print("Received:", data)
            name = data["name"]
            phone_no = data["phone"]
            datevalue = data["appt_date"]
            timevalue = data["appt_time"]
            email = data["email"]
            company_name = data["company"]
            company_url = data["url"]
            message = data["message"]

            print("name", name)
            print("phone_no", phone_no)
            print("date", datevalue)
            print("time", timevalue)
            print("email", email)
            print("company_name", company_name)
            print("company_name", company_url)
            print("message", message)

            new_appointment_uid = get_new_appointmentUID(conn)
            print("NewID = ", new_appointment_uid)
            print(getNow())

            query = '''
                INSERT INTO io.appointments
                SET appointment_uid = \'''' + new_appointment_uid + '''\',
                    appt_created_at = \'''' + getNow() + '''\',
                    name = \'''' + name + '''\',
                    phone_no = \'''' + phone_no + '''\',
                    appt_date = \'''' + datevalue + '''\',
                    appt_time = \'''' + timevalue + '''\',
                    email = \'''' + email + '''\',
                    company = \'''' + company_name + '''\',
                    url = \'''' + company_url + '''\',
                    message = \'''' + message + '''\'
                '''

            items = execute(query, "post", conn)
            print("items: ", items)
            if items["code"] == 281:
                response["message"] = "Appointments Post successful"
                return response, 200
        except:
            raise BadRequest("Request failed, please try again later.")
        finally:
            disconnect(conn)

        # ENDPOINT AND JSON OBJECT THAT WORKS
        # http://localhost:4000/api/v2/createappointment


# ADD CONTACT
class AddContact(Resource):
    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()
            data = request.get_json(force=True)
            # print to Received data to Terminal
            # print("Received:", data)

            fname = data["first_name"]
            lname = data["last_name"]
            email = data["email"]
            phone = data["phone"]
            subject = data["subject"]
            print(data)

            new_contact_uid = get_new_contactUID(conn)
            print(new_contact_uid)
            print(getNow())

            query = '''
                INSERT INTO io.contact
                SET contact_uid = \'''' + new_contact_uid + '''\',
                    contact_created_at = \'''' + getNow() + '''\',
                    first_name = \'''' + fname + '''\',
                    last_name = \'''' + lname + '''\',
                    email = \'''' + email + '''\',
                    phone = \'''' + phone + '''\',
                    subject = \'''' + subject + '''\'
                '''

            items = execute(query, "post", conn)
            print("items: ", items)
            if items["code"] == 281:
                response["message"] = "Contact Post successful"
                return response, 200
        except:
            raise BadRequest("Request failed, please try again later.")
        finally:
            disconnect(conn)


# -- ACCOUNT APIS -------------------------------------------------------------------------------

class createAccount(Resource):
    def post(self):
        response = {}
        items = []
        try:
            conn = connect()
            data = request.get_json(force=True)
            print(data)
            email = data["email"] if data.get("email") is not None else "NULL"
            firstName = data["first_name"]
            lastName = data["last_name"]
            phone = data["phone_number"] if data.get("phone_number") is not None else "NULL"
            # address = data["address"]
            # unit = data["unit"] if data.get("unit") is not None else "NULL"
            social_id = (
                data["social_id"] if data.get("social_id") is not None else "NULL"
            )
            # city = data["city"]
            # state = data["state"]
            # zip_code = data["zip_code"]
            # latitude = data["latitude"]
            # longitude = data["longitude"]
            # referral = data["referral_source"]
            role = data["role"]
            user_id = data["user_id"] if data.get("user_id") is not None else "NULL"

            if (
                    data.get("social") is None
                    or data.get("social") == "FALSE"
                    or data.get("social") == False
                    or data.get("social") == "NULL"
            ):
                social_signup = False
            else:
                social_signup = True

            print(social_signup)
            get_user_id_query = "CALL new_user_uid();"
            NewUserIDresponse = execute(get_user_id_query, "get", conn)

            print("New User info: ", NewUserIDresponse)

            if NewUserIDresponse["code"] == 490:
                string = " Cannot get new User id. "
                print("*" * (len(string) + 10))
                print(string.center(len(string) + 10, "*"))
                print("*" * (len(string) + 10))
                response["message"] = "Internal Server Error."
                return response, 500

            NewUserID = NewUserIDresponse["result"][0]["new_id"]
            print("New User ID: ", NewUserID)

            if social_signup == False:

                salt = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

                password = sha512((data["password"] + salt).encode()).hexdigest()
                print("password------", password)
                algorithm = "SHA512"
                mobile_access_token = "NULL"
                mobile_refresh_token = "NULL"
                user_access_token = "NULL"
                user_refresh_token = "NULL"
                user_social_signup = "NULL"
            else:

                mobile_access_token = data["mobile_access_token"]
                mobile_refresh_token = data["mobile_refresh_token"]
                user_access_token = data["user_access_token"]
                user_refresh_token = data["user_refresh_token"]
                salt = "NULL"
                password = "NULL"
                algorithm = "NULL"
                user_social_signup = data["social"]

                print("ELSE- OUT")

            if user_id != "NULL" and user_id:

                NewUserID = user_id

                query = (
                        """
                        SELECT user_access_token, user_refresh_token, mobile_access_token, mobile_refresh_token 
                        FROM wwp.user
                        WHERE user_uid = \'""" + user_id + """\';
                    """
                )
                it = execute(query, "get", conn)
                print("it-------", it)

                if it["result"][0]["user_access_token"] != "FALSE":
                    user_access_token = it["result"][0]["user_access_token"]

                if it["result"][0]["user_refresh_token"] != "FALSE":
                    user_refresh_token = it["result"][0]["user_refresh_token"]

                if it["result"][0]["mobile_access_token"] != "FALSE":
                    mobile_access_token = it["result"][0]["mobile_access_token"]

                if it["result"][0]["mobile_refresh_token"] != "FALSE":
                    mobile_refresh_token = it["result"][0]["mobile_refresh_token"]

                customer_insert_query = [
                    """
                        UPDATE wwp.user 
                        SET 
                        user_timestamp = \'""" + (datetime.now()).strftime("%Y-%m-%d %H:%M:%S") + """\',
                        user_first_name = \'""" + firstName + """\',
                        user_last_name = \'""" + lastName + """\',
                        user_phone = \'""" + phone + """\',
                        user_email = \'""" + email + """\'
                        user_password_salt = \'""" + salt + """\',
                        user_password_hashed = \'""" + password + """\',
                        user_password_algorithm = \'""" + algorithm + """\',
                        role = \'""" + role + """\',
                        user_social_media = \'""" + user_social_signup + """\',
                        social_timestamp  =  DATE_ADD(now() , INTERVAL 14 DAY)
                        WHERE user_uid = \'""" + user_id + """\';
                    """
                ]
                '''
                    customer_address = \'""" + address + """\',
                        customer_unit = \'""" + unit + """\',
                        customer_city = \'""" + city + """\',
                        customer_state = \'""" + state + """\',
                        customer_zip = \'""" + zip_code + """\',
                        customer_lat = \'""" + latitude + """\',
                        customer_long = \'""" + longitude + """\',
                        referral_source = \'""" + referral + """\',
                '''

            else:

                # check if there is a same customer_id existing
                query = (
                        """
                        SELECT user_email FROM wwp.user
                        WHERE user_email = \'"""
                        + email
                        + "';"
                )
                print("email---------")
                items = execute(query, "get", conn)
                if items["result"]:
                    items["result"] = ""
                    items["code"] = 409
                    items["message"] = "Email address has already been taken."

                    return items

                if items["code"] == 480:
                    items["result"] = ""
                    items["code"] = 480
                    items["message"] = "Internal Server Error."
                    return items

                print("Before write")
                # write everything to database
                customer_insert_query = [
                    """
                        INSERT INTO wwp.user
                        SET                        
                            user_uid = \'""" + NewUserID + """\',
                            user_timestamp = \'""" + (datetime.now()).strftime("%Y-%m-%d %H:%M:%S") + """\',
                            user_first_name = \'""" + firstName + """\',
                            user_last_name = \'""" + lastName + """\',
                            user_phone = \'""" + phone + """\',
                            user_email = \'""" + email + """\',
                            user_password_salt = \'""" + salt + """\',
                            user_password_hashed = \'""" + password + """\',
                            user_password_algorithm = \'""" + algorithm + """\',
                            role = \'""" + role + """\',
                            user_social_media = \'""" + user_social_signup + """\',
                            user_access_token = \'""" + user_access_token + """\',
                            social_timestamp = DATE_ADD(now() , INTERVAL 14 DAY),
                            user_refresh_token = \'""" + user_refresh_token + """\',
                            mobile_access_token = \'""" + mobile_access_token + """\',
                            mobile_refresh_token = \'""" + mobile_refresh_token + """\',
                            user_social_media_id = \'""" + social_id + """\';"""
                ]
            # print(customer_insert_query[0])
            items = execute(customer_insert_query[0], "post", conn)
            print("user_insert_query response: ", items)

            if items["code"] != 281:
                items["result"] = ""
                items["code"] = 480
                items["message"] = "Error while inserting values in database"
                return items 

                
            elif items["code"] == 281:
                items["result"] = {
                    "first_name": firstName,
                    "last_name": lastName,
                    "user_uid": NewUserID,
                    "user_access_token": user_access_token,
                    "user_refresh_token": user_refresh_token,
                    "mobile_access_token": mobile_access_token,
                    "mobile_refresh_token": mobile_refresh_token,
                    "user_social_media_id": social_id,
                }
                items["message"] = "Signup successful"
                items["code"] = 200
            
                return items

            print("sss-----", social_signup)

            # generate coupon for new user

            # query = ["CALL io.new_coupons_uid;"]
            # couponIDresponse = execute(query[0], "get", conn)
            # couponID = couponIDresponse["result"][0]["new_id"]
            # EndDate = date.today() + timedelta(days=30)
            # exp_time = str(EndDate) + " 00:00:00"

            # query = (
            #     """
            #         INSERT INTO io.coupons
            #         (
            #             coupon_uid,
            #             coupon_id,
            #             valid,
            #             discount_percent,
            #             discount_amount,
            #             discount_shipping,
            #             expire_date,
            #             limits,
            #             notes,
            #             num_used,
            #             recurring,
            #             email_id,
            #             cup_business_uid,
            #             threshold
            #         )
            #         VALUES
            #         (
            #             \'"""+ couponID+ """\',
            #             'NewCustomer',
            #             'TRUE',
            #             '0',
            #             '0',
            #             '5',
            #             \'"""+ exp_time+ """\',
            #             '1',
            #             'Welcome Coupon',
            #             '0',
            #             'F',
            #             \'"""+ email+ """\',
            #             'null',
            #             '0'
            #         );
            #         """
            # )
            # print(query)
            # item = execute(query, "post", conn)
            # if item["code"] != 281:
            #     item["message"] = "check sql query for coupons"
            #     item["code"] = 400
            #     return item
            # return items

        except:
            print("Error happened while Sign Up")
            if "NewUserID" in locals():
                execute(
                    """DELETE FROM customers WHERE customer_uid = '"""
                    + NewUserID
                    + """';""",
                    "post",
                    conn,
                )
            raise BadRequest("Request failed, please try again later.")
        finally:
            disconnect(conn)


class accountsalt(Resource):
    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()

            data = request.get_json(force=True)
            print(data)
            email = data["email"]
            query = (
                    """
                    SELECT user_password_algorithm, 
                            user_password_salt,
                            user_social_media 
                    FROM wwp.user
                    WHERE user_email = \'""" + email + """\';
                """
            )
            items = execute(query, "get", conn)
            print(items)
            if not items["result"]:
                items["message"] = "Email doesn't exists"
                items["code"] = 404
                return items
            if items["result"][0]["user_social_media"] != "NULL":
                items["message"] = (
                        """Social Signup exists. Use \'"""
                        + items["result"][0]["user_social_media"]
                        + """\' """
                )
                items["code"] = 401
                return items
            items["message"] = "SALT sent successfully"
            items["code"] = 200
            return items
        except:
            raise BadRequest("Request failed, please try again later.")
        finally:
            disconnect(conn)


class login(Resource):
    def post(self):
        response = {}
        try:
            conn = connect()
            data = request.get_json(force=True)
            print(data)
            email = data["email"]
            password = data.get("password")
            social_id = data.get("social_id")
            signup_platform = data.get("signup_platform")
            query = (
                    """
                    # CUSTOMER QUERY 1: LOGIN
                    SELECT user_uid,
                        user_last_name,
                        user_first_name,
                        user_email,
                        user_password_hashed,
                        email_verified,
                        user_social_media,
                        user_access_token,
                        user_refresh_token,
                        user_access_token,
                        user_refresh_token,
                        user_social_media_id
                    FROM wwp.user
                    WHERE user_email = \'""" + email + """\';
                """
            )
            items = execute(query, "get", conn)
            print("Password", password)
            print(items)

            if items["code"] != 280:
                response["message"] = "Internal Server Error."
                response["code"] = 500
                return response
            elif not items["result"]:
                items["message"] = "Email Not Found. Please signup"
                items["result"] = ""
                items["code"] = 404
                return items
            else:
                print(items["result"])
                print("sc: ", items["result"][0]["user_social_media_id"])

                # checks if login was by social media
                if (
                        password
                        and items["result"][0]["user_social_media_id"] != "NULL"
                        and items["result"][0]["user_social_media_id"] != None
                ):
                    response["message"] = "Need to login by Social Media"
                    response["code"] = 401
                    return response

                # nothing to check
                elif (password is None and social_id is None) or (
                        password is None
                        and items["result"][0]["user_social_media_id"] == "NULL"
                ):
                    response["message"] = "Enter password else login from social media"
                    response["code"] = 405
                    return response

                # compare passwords if user_social_media is false
                elif (
                        items["result"][0]["user_social_media_id"] == "NULL"
                        or items["result"][0]["user_social_media_id"] == None
                ) and password is not None:

                    if items["result"][0]["user_password_hashed"] != password:
                        items["message"] = "Wrong password"
                        items["result"] = ""
                        items["code"] = 406
                        return items

                    if ((items["result"][0]["email_verified"]) == "0") or (
                            items["result"][0]["email_verified"] == "FALSE"
                    ):
                        response["message"] = "Account need to be verified by email."
                        response["code"] = 407
                        return response

                # compare the social_id because it never expire.
                elif (items["result"][0]["user_social_media_id"]) != "NULL":

                    if signup_platform != items["result"][0]["user_social_media"]:
                        items["message"] = (
                                "Wrong social media used for signup. Use '"
                                + items["result"][0]["user_social_media"]
                                + "'."
                        )
                        items["result"] = ""
                        items["code"] = 411
                        return items

                    if items["result"][0]["user_social_media_id"] != social_id:
                        print(items["result"][0]["user_social_media_id"])

                        items["message"] = "Cannot Authenticated. Social_id is invalid"
                        items["result"] = ""
                        items["code"] = 408
                        return items

                else:
                    string = " Cannot compare the password or social_id while log in. "
                    print("*" * (len(string) + 10))
                    print(string.center(len(string) + 10, "*"))
                    print("*" * (len(string) + 10))
                    response["message"] = string
                    response["code"] = 500
                    return response
                del items["result"][0]["user_password_hashed"]
                del items["result"][0]["email_verified"]

                query = (
                        "SELECT * from wwp.user WHERE user_email = '" + email + "';"
                )
                items = execute(query, "get", conn)
                items["message"] = "Authenticated successfully."
                items["code"] = 200
                return items

        except:
            raise BadRequest("Request failed, please try again later.")
        finally:
            disconnect(conn)


class stripe_key(Resource):

    def get(self, desc):
        print(desc)
        if desc == 'IOTEST':
            return {'publicKey': stripe_public_test_key}
        else:
            return {'publicKey': stripe_public_live_key}


# ===========================================================
# Define API routes
api.add_resource(SignUp, '/api/v2/SignUp')

# reference APIs

api.add_resource(CreateAppointment, "/api/v2/createAppointment")
api.add_resource(AvailableAppointments, "/api/v2/availableAppointments/<string:date_value>")
api.add_resource(AddContact, "/api/v2/addContact")

api.add_resource(createAccount, "/api/v2/createAccount")
api.add_resource(accountsalt, "/api/v2/accountsalt")
api.add_resource(login, "/api/v2/login/")
api.add_resource(stripe_key, '/api/v2/stripe_key/<string:desc>')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=4000)
    # app.run(host='0.0.0.0', port=2000)
