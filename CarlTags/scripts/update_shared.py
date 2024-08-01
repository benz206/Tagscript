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
        for tag_link in open("scripts/show_off_tags.txt", "r").readlines():
            tag_id = tag_link.split("/")[-1].strip()
            await self.TAGDB.find_one_and_update(
                {"id": int(tag_id)},
                {"$set": {"shared": True}},
            )
            print("Updated " + tag_id)


turtle = Turtle()

loop.run_until_complete(turtle.start())
