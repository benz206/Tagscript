"""
This is meant to scan tags and look for new made tags and then of course update the database, it is meant to be ran at all times.
"""

import asyncio
import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
import aiohttp
from dotenv import load_dotenv
from colorama import Style, Fore
from discord_webhook import DiscordWebhook, DiscordEmbed


"""
My thought process on how this will work.

With around 30k tags at this time of this making

30,000 tags at 1 request per 3 seconds is around 24 hours. meaning every tag should be updated at least once day.

The Turtle will get the last 1,500 (Most we've gone without a tag found in recent searches is around 500)

1,500 at 1 second each is around 25 minutes meaning we should have a 25 minute window to not miss the latest tag created.

"""

load_dotenv()
loop = asyncio.get_event_loop()


async def get_current_doc_amount(TAGDB):
    """Get the current docs amount"""
    return await TAGDB.count_documents({})


async def async_range(x, y) -> int:
    """
    async range
    """
    for i in range(x, y):
        yield (i)


class FishHook:
    """
    The webhook sender
    """

    def __init__(self) -> None:
        self.ftl_updates = []
        self.rtl_updates = []

    async def update_ftl(self, index: int) -> None:
        """
        Send an update to ftl if needed
        """
        if index % 1000 == 0:
            webhook = DiscordWebhook(
                url=f"https://discord.com/api/webhooks/{os.getenv('webhook')}",
                rate_limit_retry=True,
            )
            visual = f"{Style.RESET_ALL}\n{Fore.MAGENTA}".join(self.ftl_updates)

            webhook.set_content(
                f"""```ansi
{Fore.RED}{len(self.ftl_updates)} tags have been deleted.{Style.RESET_ALL}
{visual}
```"""
            )

            webhook.execute()
        return

    async def update_rtl(self, index: int, rrange) -> None:
        """
        Send an update to ftl if needed
        """
        if index % 1500 == 0:
            webhook = DiscordWebhook(
                url=f"https://discord.com/api/webhooks/{os.getenv('webhook')}",
                rate_limit_retry=True,
            )
            visual = f"{Style.RESET_ALL}\n{Fore.BLUE}".join(self.ftl_updates)

            webhook.set_content(
                f"""```ansi
{Fore.GREEN}{len(self.ftl_updates)} tags have been found.{Style.RESET_ALL}{Fore.MAGENTA}{str(rrange):,}-{str(rrange + 1500):,}{Style.RESET_ALL}
{visual}
```"""
            )

            webhook.execute()
        return

    async def start_msg(self, msg) -> None:
        """
        Start the ftl/rtl
        """
        webhook = DiscordWebhook(
            url=f"https://discord.com/api/webhooks/{os.getenv('webhook')}",
            rate_limit_retry=True,
        )
        webhook.add_embed(DiscordEmbed(title=f"Starting {msg}", color="00FF00"))
        webhook.execute()

    async def error(self, msg) -> None:
        """
        When an error occurs
        """
        webhook = DiscordWebhook(
            url=f"https://discord.com/api/webhooks/{os.getenv('webhook')}",
            rate_limit_retry=True,
        )
        webhook.add_embed(
            DiscordEmbed(
                title=f"Error",
                description=f"""```ansi
{msg}
```""",
                color="FF0000",
            )
        )
        webhook.execute()


class Turtle:
    """
    This is for carl so why not call it turtle"""

    def __init__(self) -> None:
        self.api_url = "https://carl.gg/api/v1/tags/"
        connection_string = f"mongodb+srv://{os.environ['Mongo_User']}:{os.environ['Mongo_Pass']}@carltagscluster.nyxt2.mongodb.net/TagDB?retryWrites=true&w=majority"
        self.MONGODB = AsyncIOMotorClient(connection_string)
        self.TAGDB = self.MONGODB["TagDB"]["Tags"]
        self.hook = FishHook()

        print(f"{Fore.GREEN}Connected to DB{Style.RESET_ALL}")

    async def start(self) -> None:
        """
        Start the Turtle
        """
        self.doc_amount = await get_current_doc_amount(self.TAGDB)

        print(f"Starting turtle.")
        async with aiohttp.ClientSession() as ses:
            loop.create_task(self.recon_tag_loop(ses))
            await self.recon_tag_loop(ses)

    async def rs_TAGDB(self, _id, ses) -> None:
        """
        Request and Save a tags data to our db
        """
        try:
            async with ses.get(self.api_url + str(_id)) as tag:
                if tag.status == 404:
                    await self.TAGDB.update_one(
                        {"_id": int(_id)}, {"$set": {"deleted": True}}
                    )

                elif tag.status == 200:
                    data = await tag.json()
                    document = {
                        "_id": data.get("id"),
                        "created_at": data.get("created_at", None),
                        "guild_id": data.get("location_id", None),
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
                    self.hook.ftl_updates.append(str(_id))
                    print(
                        f"Updated Tag ID: {Fore.CYAN}{data.get('id')}{Style.RESET_ALL}"
                    )
                else:
                    print(f"{Fore.RED}{str(tag.status)} Failed.{Style.RESET_ALL}")
                    loop.create_task(self.hook.error(
                        f"{Fore.RED}{str(tag.status)} Failed.{Style.RESET_ALL}"
                    ))
                    await asyncio.sleep(5.0)
                    loop.create_task(self.rs_TAGDB(_id, ses))
        except:
            print(f"{Fore.RED}Encountered Random Error.{Style.RESET_ALL}")
            loop.create_task(self.hook.error(
                f"{Fore.RED}Encountered Random Error.{Style.RESET_ALL}"
            ))
            return

    async def s_TAGDB(self, _id, ses) -> None:
        """
        Attempt to save a tag to our db
        """
        try:
            async with ses.get(self.api_url + str(_id)) as tag:
                if tag.status == 404:
                    return

                elif tag.status == 200:
                    data = await tag.json()
                    document = {
                        "_id": data.get("id"),
                        "created_at": data.get("created_at", None),
                        "guild_id": data.get("location_id", None),
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
                    self.hook.rtl_updates.append(str(_id))
                    print(
                        f"Found new tag ID: {Fore.CYAN}{data.get('id')}{Style.RESET_ALL}"
                    )
                else:
                    print(f"{Fore.RED}{str(tag.status)} Failed.{Style.RESET_ALL}")
                    loop.create_task(self.hook.error(
                        f"{Fore.RED}{str(tag.status)} Failed.{Style.RESET_ALL}"
                    ))
                    await asyncio.sleep(5.0)
                    loop.create_task(self.s_TAGDB(_id, ses))
        except:
            print(f"{Fore.RED}Encountered Random Error.{Style.RESET_ALL}")
            loop.create_task(self.hook.error(
                f"{Fore.RED}Encountered Random Error.{Style.RESET_ALL}"
            ))
            return

    async def full_tag_loop(self, ses) -> None:
        """
        Full tag loop, reupdates all tags
        """
        while True:
            loop.create_task(self.hook.start_msg("FTL"))
            self.ftlc = 0
            async for tag in self.TAGDB.find({"deleted": False}):
                self.ftlc += 1
                loop.create_task(self.hook.update_ftl(self.ftlc))
                loop.create_task(self.rs_TAGDB(tag.get("_id"), ses))
                await asyncio.sleep(3.0)

    async def recon_tag_loop(self, ses) -> None:
        """
        Recon for new tags, will continuosly search for more tags
        """
        while True:
            loop.create_task(self.hook.start_msg("RTL"))
            self.rtlc = 0
            cursor = self.TAGDB.find({}).sort("_id", -1)
            for tag in await cursor.to_list(length=1):
                latest = tag.get("_id")

            async for i in async_range(1, 1500):
                self.rtlc += 1
                loop.create_task(self.hook.update_rtl(self.rtlc, latest))
                _id = latest + i
                loop.create_task(self.s_TAGDB(_id, ses))
                await asyncio.sleep(1.0)


turtle = Turtle()

loop.run_until_complete(turtle.start())
