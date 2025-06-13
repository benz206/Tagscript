"""
This script performs a one-time deep scan to find and update latest tags up to 100,000 tags.
"""

import asyncio
import os

import aiohttp
from colorama import Fore, Style
from discord_webhook import DiscordEmbed, DiscordWebhook
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()
loop = asyncio.new_event_loop()

class FishHook:
    """
    The webhook sender
    """
    def __init__(self) -> None:
        self.rtl_updates = []
        self.rtl_loops = 0

    async def update_rtl(self, rrange: int) -> None:
        """
        Send an update to our webhook when we want one
        """
        webhook = DiscordWebhook(
            url=f"https://discord.com/api/webhooks/{os.getenv('webhook')}",
            rate_limit_retry=True,
        )
        visual = "\n- ".join(self.rtl_updates)
        await asyncio.sleep(3)
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

    async def send_starting_message(self) -> None:
        """
        Send a starting message to the webhook
        """
        webhook = DiscordWebhook(
            url=f"https://discord.com/api/webhooks/{os.getenv('webhook')}",
        )
        webhook.add_embed(
            DiscordEmbed(
                title="Starting Deep Scan",
                description=f"""```ansi
{Fore.GREEN}Starting Deep Scan{Style.RESET_ALL}
```""",
            )
        )
        webhook.execute()
        await asyncio.sleep(3)
        return

    async def send_ending_message(self) -> None:
        """
        Send an ending message to the webhook
        """
        webhook = DiscordWebhook(
            url=f"https://discord.com/api/webhooks/{os.getenv('webhook')}",
        )
        webhook.add_embed(
            DiscordEmbed(
                title="Deep Scan Complete",
                description=f"""```ansi
{Fore.GREEN}Deep Scan Completed{Style.RESET_ALL}
```""",
            )
        )
        webhook.execute()

class DeepScanner:
    """
    Scanner for performing a deep scan of tags
    """
    def __init__(self) -> None:
        self.api_url = "https://carl.gg/api/v1/tags/"
        connection_string = f"mongodb+srv://{os.environ['Mongo_User']}:{os.environ['Mongo_Pass']}@carltagscluster.nyxt2.mongodb.net/TagDB?retryWrites=true&w=majority"
        self.MONGODB = AsyncIOMotorClient(connection_string)
        self.TAGDB = self.MONGODB["TagDB"]["Tags"]
        self.hook = FishHook()
        print(f"{Fore.GREEN}Connected to DB{Style.RESET_ALL}")

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
                    await asyncio.sleep(7.5)
                    loop.create_task(self.s_TAGDB(_id, ses))
        except:
            print(f"{Fore.RED}Encountered Random Error.{Style.RESET_ALL}")
            await asyncio.sleep(7.5)
            return

    async def start(self) -> None:
        """
        Start the deep scan
        """
        print(f"{Fore.YELLOW}Starting deep scan for latest tags...{Style.RESET_ALL}")
        await self.hook.send_starting_message()
        
        async with aiohttp.ClientSession() as ses:
            cursor = self.TAGDB.find({}, {"id": 1}).sort("id", -1)
            for tag in await cursor.to_list(length=1):
                latest = tag.get("id")
            
            task_count = 0
            for i in range(1, 100001):  # Scan up to 100,000 tags
                _id = latest + i
                loop.create_task(self.s_TAGDB(_id, ses))
                task_count += 1
                await asyncio.sleep(0.05)
                
                if task_count % 1000 == 0:
                    loop.create_task(self.hook.update_rtl(latest))
                    await asyncio.sleep(3)
            
            await self.hook.send_ending_message()
            print(f"{Fore.GREEN}Deep scan completed!{Style.RESET_ALL}")

scanner = DeepScanner()
loop.run_until_complete(scanner.start())
