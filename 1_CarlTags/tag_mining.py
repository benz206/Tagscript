"""
No as far as I'm aware this is not illegal
Devs are aware that this endpoint exists and that the community knows (Carl-bot patrons and vips channel "see-ers" at least)

I am not making this to try and break or for complete data collection *

* Note I am requesting the following information from following api endpoint
https://carl.gg/api/v1/tags/TAGID

created_at
tag_id
location_id
name
nsfw
owner_id
sharer (Basically the same as owner_id id unless the person who shared it isn't the same)
uses

Everyone. Will be able to access the data
Everyone. Is already able to access the data through the above endpoint
Everyone. May ask me to delete tags that they own.
This is meant as a fun project for me! Enjoy!
"""

import asyncio
from flask import Flask
from motor.motor_asyncio import AsyncIOMotorClient
import os
import requests
from threading import Thread
import time
import urllib


"""
Tag Schema
{
    _id: tag_id,
    created_at: created_at,
    guild_id: location_id,
    tag_name: name, # cut down to 25 characters max
    nsfw: true/false,
    owner_id: owner_id,
    sharer: shared_id,
    uses: int
}
"""

async def get_current_tag_id(MONGODB):
    """Get the current tags id"""
    tag = await MONGODB["TagDB"]["Config"].find_one({"config": "config"})
    return(int(tag.get("count")))

async def get_current_doc_amount(TAGDB):
    """Get the current docs amount"""
    return await TAGDB.count_documents({})


class TagscriptMiner:
    """Mining and tracking tag information"""

    def __init__(self) -> None:
        self.api_url = "https://carl.gg/api/v1/tags/"
        self.loop = asyncio.get_event_loop()
        
        connection_string = f"mongodb+srv://{os.environ['Mongo_User']}:{os.environ['Mongo_Pass']}@carltagscluster.nyxt2.mongodb.net/TagDB?retryWrites=true&w=majority"
        self.MONGODB = AsyncIOMotorClient(connection_string)
        self.TAGDB = self.MONGODB["TagDB"]["Tags"]
        self.count = self.loop.run_until_complete(get_current_tag_id(self.MONGODB))
        self.doc_amount = self.loop.run_until_complete(get_current_doc_amount(self.TAGDB))
        print("Connected to DB")


    async def save_TagDB(self, data: dict) -> None:
        """Save a tags data to our db"""
        document = {
            "_id": data.get("id"),
            "created_at": data.get("created_at", None),
            "guild_id": data.get("location_id", None),
            "tag_name": data.get("name")[:25],
            "nsfw": data.get("nsfw", None),
            "owner_id": data.get("owner_id", None),
            "sharer": data.get("sharer", None),
            "uses": data.get("uses", 0)
        }
        result = await self.TAGDB.insert_one(document)
        print(f"Saved Tag ID: {repr(result.inserted_id)} to database")

    async def save_current_count(self):
        """Save the current count"""
        config = self.MONGODB["TagDB"]["Config"]
        print(f"Saved count at Tag ID: {self.count}")
        doc_amount = await self.TAGDB.count_documents({})
        print(f"Current Amount of Tags Saved in Database: {doc_amount:,} (+{doc_amount - self.doc_amount} Tags)")
        self.doc_amount = doc_amount
        await config.update_one({"config": "config"}, {"$set": {"count": self.count}})


    def store_data(self):
        """The function to start storing the data"""
        try:
            tag = requests.get(self.api_url + str(self.count))
        except:
            # if for some reason something goes wrong when requesting
            print("Encountered 104, sleeping for 3 seconds")
            time.sleep(3)
            return
        #print(f"Attempting to save Tag ID: {str(self.count)}")
        self.count += 1
        if (self.count % 100) == 0:
            self.loop.run_until_complete(self.save_current_count())
        if tag.status_code == 404:
            time.sleep(0.05)
            #print(f"Non Existent")
        elif tag.status_code == 200:
            self.loop.run_until_complete(self.save_TagDB(tag.json()))
            time.sleep(0.05)
        else:
            print(str(tag.status_code) + " failed. not sure why")
            time.sleep(3)
            return


app = Flask(__name__)
@app.route("/")	
def home():
	return {"status": "Alive"}

def run():
    app.run(host="0.0.0.0", port=8080)

server = Thread(target=run)
server.start()

async def keep_alive():
    while 1:
        urllib.request.urlopen("https://Dataminer.tagscript1.repl.co")
        await asyncio.sleep(200)

keep_alive()

miner = TagscriptMiner()
print(f"Starting miner.\n Continuing at Tag ID: {miner.count}")

while True:
    miner.store_data()
