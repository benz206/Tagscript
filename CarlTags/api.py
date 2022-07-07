"""
This is a completely public api 
"""

import asyncio
import os

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from motor.motor_asyncio import AsyncIOMotorClient

app = Flask(__name__)
loop = asyncio.get_event_loop()

connection_string = f"mongodb+srv://{os.environ['Mongo_User']}:{os.environ['Mongo_Pass']}@carltagscluster.nyxt2.mongodb.net/TagDB?retryWrites=true&w=majority"
MONGODB = AsyncIOMotorClient(connection_string)
TAGDB = MONGODB["TagDB"]["Tags"]

limiter = Limiter(app, key_func=get_remote_address, default_limits=["50 per second"])


@app.route("/update/<int:tagid>")
@limiter.limit("1 per day")
def update(tagid):
    """
    Think a tag we have in our database isn't accurate?

    Request this endpoint to update our db
    """
    return {"Status": "Not finished"}


@app.route("/medium")
@limiter.limit("1/second", override_defaults=False)
def medium():
    return ":|"


@app.route("/fast")
def fast():
    return ":)"


@app.route("/ping")
@limiter.exempt
def ping():
    return "PONG"
