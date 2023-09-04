"""
This is meant to scan tags and look for new made tags and then of course update the database, it is meant to be ran at all times.
"""

import asyncio
import datetime
import os

import aiohttp
from colorama import Fore, Style
from discord_webhook import DiscordEmbed, DiscordWebhook
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()
loop = asyncio.get_event_loop()


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
        self.rtl_loops = 0

    async def update_ftl(self) -> None:
        """
        Send an update to ftl if needed
        """
        webhook = DiscordWebhook(
            url=f"https://discord.com/api/webhooks/{os.getenv('webhook')}",
            rate_limit_retry=True,
        )
        len_ftl = len(self.ftl_updates)
        self.ftl_visual = []

        for i in range(round(len(self.ftl_updates) / 220) - 1):
            temp = []
            for i in range(
                220
            ):  # Numer of ids we should be able to fit into the message
                temp.append(self.ftl_updates[0])
                self.ftl_updates.pop(0)

            try:
                webhook.set_content(
                    f"""```ansi
{Fore.BLUE} {", ".join(temp)} {Style.RESET_ALL}
```"""
                )
                webhook.execute()
            except:
                pass

        if self.ftl_updates:
            webhook.set_content(
                f"""```ansi
{Fore.BLUE}{", ".join(self.ftl_updates)}{Style.RESET_ALL}
```"""
            )
            webhook.execute()

        webhook.set_content(
            f"""```ansi
{Fore.RED}{len_ftl} tags have been updated.{Style.RESET_ALL}
```"""
        )
        webhook.execute()
        self.ftl_updates = []
        return

    async def update_rtl(self, rrange: int) -> None:
        """
        Send an update to our webhook when we want one
        """
        webhook = DiscordWebhook(
            url=f"https://discord.com/api/webhooks/{os.getenv('webhook')}",
            rate_limit_retry=True,
        )
        visual = "\n- ".join(self.rtl_updates)
        if self.rtl_updates:
            webhook.set_content(
                f"""```ansi
{Fore.GREEN}{len(self.rtl_updates)} tag(s) have been found. ( {self.rtl_loops} loops have completed since last search )

{Fore.MAGENTA}Old Search Range: {rrange:,}-{(rrange + 1500):,}
{Fore.YELLOW}New Search Range: {int(self.rtl_updates[-1]):,}-{(int(self.rtl_updates[-1]) + 1500):,}

{Fore.BLUE}- {visual}
```"""
            )
            self.rtl_updates = []
            self.rtl_loops = 0
            webhook.execute()
            return
        self.rtl_loops += 1

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
                title="Error",
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
        self.TAGDB = self.MONGODB["TagDB"]["NewTags"]
        self.hook = FishHook()

        print(f"{Fore.GREEN}Connected to DB{Style.RESET_ALL}")

    async def start(self) -> None:
        """
        Start the Turtle
        """
        print("Starting turtle.")
        async with aiohttp.ClientSession() as ses:
            loop.create_task(self.full_tag_loop(ses))
            await self.recon_tag_loop(ses)

    async def rs_TAGDB(self, _id, ses) -> None:
        """
        Request and Save a tags data to our db
        """
        try:
            async with ses.get(self.api_url + str(_id)) as tag:
                if tag.status == 404:
                    await self.TAGDB.update_one(
                        {"id": int(_id)}, {"$set": {"deleted": True}}
                    )

                elif tag.status == 200:
                    data = await tag.json()
                    tag = await self.TAGDB.find_one({"id": int(_id)})

                    if "{=(PRIVATE):true}" in data.get("content"):
                        deleted = True
                    else:
                        deleted = data.get("deleted")

                    if (
                        data.get("id") == tag.get("id")
                        and data.get("name") == tag.get("tag_name")
                        and data.get("nsfw") == tag.get("nsfw")
                        and data.get("owner_id") == tag.get("owner_id")
                        and data.get("sharer") == tag.get("sharer")
                        and data.get("uses") == tag.get("uses")
                        and data.get("content") == tag.get("content")
                        and data.get("embed") == tag.get("embed")
                    ):
                        await self.TAGDB.update_one(
                            {"id": int(_id)},
                            {"$set": {"last_fetched": datetime.datetime.utcnow()}},
                        )

                    else:
                        document = {
                            "id": data.get("id"),
                            "created_at": datetime.datetime.strptime(
                                data.get("created_at"), "%a, %d %b %Y %H:%M:%S GMT"
                            ),
                            "guild_id": str(data.get("location_id", None)),
                            "tag_name": data.get("name"),
                            "nsfw": data.get("nsfw", None),
                            "owner_id": data.get("owner_id", None),
                            "sharer": data.get("sharer", None),
                            "uses": data.get("uses", 0),
                            "content": data.get("content", ""),
                            "embed": data.get("embed", ""),
                            "last_fetched": datetime.datetime.utcnow(),
                            "deleted": deleted,
                            "description": data.get("description", None),
                            "restricted": data.get("restricted", False),
                        }
                        quick_query = {"id": data.get("id")}
                        await self.TAGDB.replace_one(quick_query, document, True)
                        self.hook.ftl_updates.append(str(_id))
                        print(
                            f"Updated Tag ID: {Fore.CYAN}{data.get('id')}{Style.RESET_ALL}"
                        )
                else:
                    # print(f"{Fore.RED}{str(tag.status)} Failed.{Style.RESET_ALL}")
                    await asyncio.sleep(7.5)
                    loop.create_task(self.rs_TAGDB(_id, ses))
        except Exception as e:
            print(f"{Fore.RED}Encountered Random Error.{Style.RESET_ALL}")
            loop.create_task(
                self.hook.error(
                    f"""{Fore.RED}Encountered Random Error.{Style.RESET_ALL}
```
```py
{e}
"""
                )
            )
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
                        "id": data.get("id"),
                        "created_at": datetime.datetime.strptime(
                            data.get("created_at"), "%a, %d %b %Y %H:%M:%S GMT"
                        ),
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
                        "description": data.get("description", None),
                        "restricted": data.get("restricted", False),
                    }
                    quick_query = {"id": data.get("id")}
                    await self.TAGDB.replace_one(quick_query, document, True)
                    self.hook.rtl_updates.append(str(_id))
                    print(
                        f"Found new tag ID: {Fore.CYAN}{data.get('id')}{Style.RESET_ALL}"
                    )
                else:
                    # print(f"{Fore.RED}{str(tag.status)} Failed.{Style.RESET_ALL}")
                    await asyncio.sleep(7.5)
                    loop.create_task(self.s_TAGDB(_id, ses))
        except:
            print(f"{Fore.RED}Encountered Random Error.{Style.RESET_ALL}")
            loop.create_task(
                self.hook.error(f"{Fore.RED}Encountered Random Error.{Style.RESET_ALL}")
            )
            return

    async def full_tag_loop(self, ses) -> None:
        """
        Full tag loop, reupdates all tags

        We have to create a list instead of iterating because when we aggregate the list,
        mongodb only keeps the data for 10 minutes max in it's cache, we cannot change
        this as we're on the free tier. Instead we'll cache the list
        """
        while True:
            self.ftl_ids = []
            async for tag in self.TAGDB.find({"deleted": False}):
                self.ftl_ids.append(tag.get("id"))
            print(
                f"Finished gathering {Fore.CYAN}{len(self.ftl_ids):,}{Style.RESET_ALL} Tag IDS"
            )

            for tag in self.ftl_ids:
                loop.create_task(self.rs_TAGDB(tag, ses))
                await asyncio.sleep(0.3)

            loop.create_task(self.hook.update_ftl())

    async def recon_tag_loop(self, ses) -> None:
        """
        Recon for new tags, will continuosly search for more tags
        """
        while True:
            self.rtlc = 0
            cursor = self.TAGDB.find({}, {"id": 1}).sort("id", -1)
            for tag in await cursor.to_list(length=1):
                latest = tag.get("id")

            async for i in async_range(1, 3000):
                self.rtlc += 1
                _id = latest + i
                loop.create_task(self.s_TAGDB(_id, ses))
                await asyncio.sleep(0.05)

            loop.create_task(self.hook.update_rtl(latest))


turtle = Turtle()

loop.run_until_complete(turtle.start())
