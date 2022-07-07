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
    This is for carl so why not call it turtle"""

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
        print(f"Starting turtle.")
        await self.fix_created_ats()

    async def fix_created_ats(self) -> None:
        """
        Full tag loop, reupdates all tags
        """
        async for tag in self.TAGDB.find({}):
            if not isinstance(tag.get("created_at"), datetime.date):
                await self.TAGDB.update_one(
                    {"_id": tag.get("_id")},
                    {
                        "$set": {
                            "created_at": datetime.datetime.strptime(
                                tag.get("created_at"), "%a, %d %b %Y %H:%M:%S GMT"
                            )
                        }
                    },
                )
                print(f"Updated {tag.get('_id')}")


turtle = Turtle()

loop.run_until_complete(turtle.start())
