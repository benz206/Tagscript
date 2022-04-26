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
content
embed

Everyone. Will be able to access the data
Everyone. Is already able to access the data through the above endpoint
Everyone. May ask me to delete tags that they own.
This is meant as a fun project for me! Enjoy!
"""

import asyncio
import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
import aiohttp
from dotenv import load_dotenv
from colorama import Style, Fore
import sys

load_dotenv()


"""
Tag Schema
{
    _id: tag_id,
    created_at: created_at,
    guild_id: location_id,
    tag_name: name,
    nsfw: true/false,
    owner_id: owner_id,
    sharer: shared_id,
    uses: int,
    "content": content,
    "embed": embed,
    "last_fetched": last_fetched,
    "deleted": deleted,
}
"""


async def get_current_tag_id(MONGODB):
    """Get the current tags id"""
    tag = await MONGODB["TagDB"]["Config"].find_one({"config": "config"})
    return int(tag.get("count"))


async def get_current_doc_amount(TAGDB):
    """Get the current docs amount"""
    return await TAGDB.count_documents({})


loop = asyncio.get_event_loop()


class TagscriptMiner:
    """Mining and tracking tag information"""

    def __init__(self) -> None:
        self.api_url = "https://carl.gg/api/v1/tags/"
        connection_string = f"mongodb+srv://{os.environ['Mongo_User']}:{os.environ['Mongo_Pass']}@carltagscluster.nyxt2.mongodb.net/TagDB?retryWrites=true&w=majority"
        self.MONGODB = AsyncIOMotorClient(connection_string)
        self.TAGDB = self.MONGODB["TagDB"]["Tags"]

        print(f"{Fore.GREEN}Connected to DB{Style.RESET_ALL}")

    async def start(self) -> None:
        """Start the bot"""

        self.count = await get_current_tag_id(self.MONGODB)
        self.doc_amount = await get_current_doc_amount(self.TAGDB)

        print(f"Starting miner.\nContinuing at Tag ID: {miner.count}")
        async with aiohttp.ClientSession() as ses:
            while True:
                await self.store_data(ses)

    async def save_TagDB(self, data: dict) -> None:
        """Save a tags data to our db"""
        document = {
            "_id": data.get("id"),
            "created_at": datetime.datetime.strptime(data.get("created_at"), "%a, %d %b %Y %H:%M:%S GMT"),
            "guild_id": str(data.get("location_id", None)),
            "tag_name": data.get("name"),
            "nsfw": data.get("nsfw", None),
            "owner_id": data.get("owner_id", None),
            "sharer": data.get("sharer", None),
            "uses": data.get("uses", 0),
            "content": data.get("content", ""),
            "embed": data.get("embed", ""),
            "last_fetched": datetime.datetime.utcnow(),
            "deleted": False,
        }
        quick_query = {"_id": data.get("id")}
        await self.TAGDB.replace_one(quick_query, document, True)
        print(f"Saved Tag ID: {Fore.CYAN}{data.get('id')}{Style.RESET_ALL}")

    async def save_current_count(self):
        """Save the current count"""
        config = self.MONGODB["TagDB"]["Config"]
        print(f"Config count saved at Tag ID: {Fore.BLUE}{self.count}{Style.RESET_ALL}")
        doc_amount = await self.TAGDB.count_documents({})
        print(
            f"Tags Saved: {Fore.MAGENTA}{doc_amount:,}{Style.RESET_ALL} ({Fore.GREEN}+ {doc_amount - self.doc_amount}{Style.RESET_ALL} Tags)"
        )
        self.doc_amount = doc_amount
        await config.update_one({"config": "config"}, {"$set": {"count": self.count}})

    async def store_data(self, ses):
        """The function to start storing the data"""
        try:
            async with ses.get(self.api_url + str(self.count)) as tag:
                # print(f"Attempting to save Tag ID: {str(self.count)}")
                self.count += 1
                if self.count > 1400000:
                    sys.exit("Finished")
                if (self.count % 500) == 0:
                    loop.create_task(self.save_current_count())
                if tag.status == 404:
                    await asyncio.sleep(0.05)
                    # print(f"Non Existent")
                elif tag.status == 200:
                    loop.create_task(self.save_TagDB(await tag.json()))
                    await asyncio.sleep(0.05)
                else:
                    print(f"{Fore.RED}{str(tag.status)} Failed.{Style.RESET_ALL}")
                    await asyncio.sleep(3)
                    return

        except:
            # if for some reason something goes wrong when requesting
            print(f"{Fore.RED}Encountered Random Error.{Style.RESET_ALL}")
            await asyncio.sleep(3)
            return


miner = TagscriptMiner()

loop.run_until_complete(miner.start())
