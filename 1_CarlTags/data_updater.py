"""A lot of the data that was saved wasn't saved in what was necessarily the best type

Current:
{
    _id: int32,
    created_at: str,
    guild_id: int64,
    tag_name: str,
    nsfw: bool,
    owner_id: str,
    sharer: str,
    uses: int32
}

New Format:
{
    _id: int32,
    created_at: Date Object, CHANGED
    guild_id: int64,
    tag_name: str,
    nsfw: bool,
    owner_id: string,
    sharer: string,
    uses: int32,
    embed: json, ADDED
    description: string, ADDED
    last_fetched: Date object, ADDED
    deleted: bool ADDED
}

"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()


loop = asyncio.get_event_loop()

connection_string = f"mongodb+srv://{os.environ['Mongo_User']}:{os.environ['Mongo_Pass']}@carltagscluster.nyxt2.mongodb.net/TagDB?retryWrites=true&w=majority"
MONGODB = AsyncIOMotorClient(connection_string)
TAGDB = MONGODB["TagDB"]["Tags"]

async def update_created_at():
    """Update created at"""
    await TAGDB.update_many(
        {},
        [{
            "$set": {
                "created_at": {
                    "$toDate": "$created_at"
                }
            }
        }]
    )


loop.run_until_complete(update_created_at())
