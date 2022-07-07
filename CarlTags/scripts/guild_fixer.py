import asyncio
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
        await self.fix_guild_ids()

    async def fix_guild_ids(self) -> None:
        """
        Full tag loop, reupdates all tags
        """
        async for tag in self.TAGDB.find({}):
            if isinstance(tag.get("guild_id"), int):
                await self.TAGDB.update_one(
                    {"_id": tag.get("_id")},
                    {"$set": {"guild_id": str(tag.get("guild_id"))}},
                )
                print(f"Updated {tag.get('_id')}")
            else:
                pass


turtle = Turtle()

loop.run_until_complete(turtle.start())
