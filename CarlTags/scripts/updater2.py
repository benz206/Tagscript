"""
An improved version of the tag updater with better rate limiting, error handling, and monitoring.
"""

import asyncio
import datetime
import os
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from collections import deque

import aiohttp
from colorama import Fore, Style
from discord_webhook import DiscordEmbed, DiscordWebhook
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from aiohttp import ClientTimeout

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

ONE_MINUTE = 60
MAX_REQUESTS_PER_MINUTE = 45
BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_DELAY = 5
TIMEOUT = ClientTimeout(total=30)

@dataclass
class TagStats:
    """Statistics for tag operations"""
    total_processed: int = 0
    new_tags: int = 0
    updated_tags: int = 0
    deleted_tags: int = 0
    errors: int = 0
    start_time: datetime.datetime = datetime.datetime.utcnow()

    def get_runtime(self) -> str:
        """Get formatted runtime duration"""
        duration = datetime.datetime.utcnow() - self.start_time
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        return f"{hours}h {minutes}m"

class RateLimiter:
    """Rate limiter for API requests"""
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()

    async def acquire(self):
        """Acquire a rate limit token"""
        now = datetime.datetime.utcnow()
        
        while self.requests and (now - self.requests[0]).total_seconds() > self.time_window:
            self.requests.popleft()
        
        if len(self.requests) >= self.max_requests:
            wait_time = self.time_window - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self.requests.append(now)

class DiscordNotifier:
    """Handles Discord webhook notifications"""
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.update_queue = deque(maxlen=1000)
        self.stats = TagStats()
        self.last_notification = datetime.datetime.utcnow()

    async def send_notification(self, content: str, embed: Optional[DiscordEmbed] = None):
        """Send a notification to Discord"""
        webhook = DiscordWebhook(url=self.webhook_url, rate_limit_retry=True)
        if embed:
            webhook.add_embed(embed)
        else:
            webhook.set_content(content)
        await asyncio.to_thread(webhook.execute)

    async def queue_update(self, tag_id: int, operation: str):
        """Queue a tag update for notification"""
        self.update_queue.append((tag_id, operation))
        if len(self.update_queue) >= 100 or (datetime.datetime.utcnow() - self.last_notification).total_seconds() > 300:
            await self.flush_updates()

    async def flush_updates(self):
        """Send queued updates to Discord"""
        if not self.update_queue:
            return

        updates = []
        while self.update_queue:
            tag_id, operation = self.update_queue.popleft()
            updates.append(f"{operation}: {tag_id}")

        content = f"```ansi\n{Fore.BLUE}Updates:\n{Fore.GREEN}{chr(10).join(updates)}{Style.RESET_ALL}\n```"
        await self.send_notification(content)
        self.last_notification = datetime.datetime.utcnow()

    async def send_stats(self):
        """Send current statistics to Discord"""
        embed = DiscordEmbed(
            title="Tag Updater Statistics",
            description=f"""```ansi
{Fore.GREEN}Runtime: {self.stats.get_runtime()}
{Fore.BLUE}Total Processed: {self.stats.total_processed:,}
{Fore.CYAN}New Tags: {self.stats.new_tags:,}
{Fore.YELLOW}Updated Tags: {self.stats.updated_tags:,}
{Fore.RED}Deleted Tags: {self.stats.deleted_tags:,}
{Fore.MAGENTA}Errors: {self.stats.errors:,}
```""",
            color="00FF00"
        )
        await self.send_notification("", embed)

class TagUpdater:
    """Main tag updater class"""
    def __init__(self):
        self.api_url = "https://carl.gg/api/v1/tags/"
        self.connection_string = f"mongodb+srv://{os.environ['Mongo_User']}:{os.environ['Mongo_Pass']}@carltagscluster.nyxt2.mongodb.net/TagDB?retryWrites=true&w=majority"
        self.mongodb = AsyncIOMotorClient(self.connection_string)
        self.tagdb = self.mongodb["TagDB"]["Tags"]
        self.notifier = DiscordNotifier(os.getenv('webhook'))
        self.rate_limiter = RateLimiter(MAX_REQUESTS_PER_MINUTE, ONE_MINUTE)
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize the updater"""
        self.session = aiohttp.ClientSession(timeout=TIMEOUT)
        await self.notifier.send_notification("```ansi\n" + Fore.GREEN + "Tag Updater Started" + Style.RESET_ALL + "\n```")

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        await self.notifier.flush_updates()
        await self.notifier.send_stats()

    async def fetch_tag(self, tag_id: int) -> Optional[Dict]:
        """Fetch a tag from the API with rate limiting and retries"""
        for attempt in range(MAX_RETRIES):
            try:
                await self.rate_limiter.acquire()
                async with self.session.get(f"{self.api_url}{tag_id}") as response:
                    if response.status == 404:
                        return None
                    if response.status == 200:
                        return await response.json()
                    if response.status == 429:
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                        continue
                    logger.error(f"Unexpected status {response.status} for tag {tag_id}")
                    return None
            except Exception as e:
                logger.error(f"Error fetching tag {tag_id}: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                continue
        return None

    async def update_tag(self, tag_id: int):
        """Update a single tag"""
        try:
            data = await self.fetch_tag(tag_id)
            if not data:
                await self.tagdb.update_one(
                    {"id": tag_id},
                    {"$set": {"deleted": True, "last_fetched": datetime.datetime.utcnow()}}
                )
                self.notifier.stats.deleted_tags += 1
                await self.notifier.queue_update(tag_id, "Deleted")
                return

            is_private = "{=(PRIVATE):true}" in data.get("content", "")
            deleted = is_private or data.get("deleted", False)

            existing_tag = await self.tagdb.find_one({"id": tag_id})
            if existing_tag:
                if self._tag_unchanged(existing_tag, data):
                    await self.tagdb.update_one(
                        {"id": tag_id},
                        {"$set": {"last_fetched": datetime.datetime.utcnow()}}
                    )
                    return

            document = self._create_tag_document(data, deleted)
            await self.tagdb.replace_one({"id": tag_id}, document, upsert=True)
            
            if existing_tag:
                self.notifier.stats.updated_tags += 1
                await self.notifier.queue_update(tag_id, "Updated")
            else:
                self.notifier.stats.new_tags += 1
                await self.notifier.queue_update(tag_id, "New")

        except Exception as e:
            logger.error(f"Error updating tag {tag_id}: {str(e)}")
            self.notifier.stats.errors += 1
        finally:
            self.notifier.stats.total_processed += 1

    def _tag_unchanged(self, existing: Dict, new: Dict) -> bool:
        """Check if tag data is unchanged"""
        fields = ["name", "nsfw", "owner_id", "sharer", "uses", "content", "embed"]
        return all(existing.get(f"tag_name" if f == "name" else f) == new.get(f) for f in fields)

    def _create_tag_document(self, data: Dict, deleted: bool) -> Dict:
        """Create a tag document from API data"""
        return {
            "id": data["id"],
            "created_at": datetime.datetime.strptime(data["created_at"], "%a, %d %b %Y %H:%M:%S GMT"),
            "guild_id": str(data.get("location_id")),
            "tag_name": data["name"],
            "nsfw": data.get("nsfw"),
            "owner_id": data.get("owner_id"),
            "sharer": data.get("sharer"),
            "uses": data.get("uses", 0),
            "content": data.get("content", ""),
            "embed": data.get("embed", ""),
            "last_fetched": datetime.datetime.utcnow(),
            "deleted": deleted,
            "description": data.get("description"),
            "restricted": data.get("restricted", False)
        }

    async def update_existing_tags(self):
        """Update all existing tags"""
        while True:
            try:
                cursor = self.tagdb.find({"deleted": False})
                async for tag in cursor:
                    await self.update_tag(tag["id"])
                    await asyncio.sleep(0.1)
                
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"Error in update_existing_tags: {str(e)}")
                await asyncio.sleep(60)

    async def scan_new_tags(self):
        """Scan for new tags"""
        while True:
            try:
                cursor = self.tagdb.find({}, {"id": 1}).sort("id", -1)
                latest_tag = await cursor.to_list(length=1)
                if not latest_tag:
                    latest_id = 0
                else:
                    latest_id = latest_tag[0]["id"]

                for i in range(1, 3000):
                    await self.update_tag(latest_id + i)
                    await asyncio.sleep(0.1)

                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error in scan_new_tags: {str(e)}")
                await asyncio.sleep(60)

    async def run(self):
        """Run the updater"""
        try:
            await self.initialize()
            await asyncio.gather(
                self.update_existing_tags(),
                self.scan_new_tags()
            )
        except Exception as e:
            logger.error(f"Fatal error in updater: {str(e)}")
        finally:
            await self.cleanup()

if __name__ == "__main__":
    updater = TagUpdater()
    asyncio.run(updater.run()) 