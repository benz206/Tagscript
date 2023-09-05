import asyncio
import datetime
import os

from colorama import Fore, Style
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()
loop = asyncio.get_event_loop()


class Turtle:
    """
    Took roughly 10 minutes to run and update all the tags at this point, had tag id 1.8 mil at this time
    """

    def __init__(self) -> None:
        self.api_url = "https://carl.gg/api/v1/tags/"
        connection_string = f"mongodb+srv://{os.environ['Mongo_User']}:{os.environ['Mongo_Pass']}@carltagscluster.nyxt2.mongodb.net/TagDB?retryWrites=true&w=majority"
        self.MONGODB = AsyncIOMotorClient(connection_string)
        self.TAGDB = self.MONGODB["TagDB"]["Tags"]
        self.NEW_TAGDB = self.MONGODB["TagDB"]["NewTags"]

        print(f"{Fore.GREEN}Connected to DB{Style.RESET_ALL}")

    async def start(self) -> None:
        """
        Start the Turtle
        """
        print("Starting turtle.")
        await self.fix_created_ats()

    async def fix_created_ats(self) -> None:
        """
        Full tag loop, reupdates all tags
        """
        async for tag in self.NEW_TAGDB.find({}):
            # if not isinstance(tag.get("created_at"), datetime.date):
            #     await self.TAGDB.update_one(
            #         {"_id": tag.get("_id")},
            #         {
            #             "$set": {
            #                 "created_at": datetime.datetime.strptime(
            #                     tag.get("created_at"), "%a, %d %b %Y %H:%M:%S GMT"
            #                 )
            #             }
            #         },
            #     )
            #     print(f"Updated {tag.get('_id')}")
            tag["shared"] = False
            tag["safe"] = "unrated  "
            await self.TAGDB.insert_one(tag)
            print(f"Inserted {tag.get('id')}")

turtle = Turtle()

loop.run_until_complete(turtle.start())
