"""
MIT License

Copyright (c) 2022 Ben

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
"""


import asyncio
import datetime
import json
import sys
import urllib.request
from random import randint
from threading import Thread

import PIL as pil
import requests
from flask import Flask, send_file


class Tag:
    """
    Class for a tag and all its info
    """

    __slots__ = (
        "tag_id",
        "name",
        "content",
        "owner",
        "sharer",
        "nsfw",
        "restricted",
        "created_at",
        "description",
        "embed",
        "location",
        "uses",
    )

    def __init__(self, _json: dict) -> None:
        """
        Construct the tag
        """
        self.tag_id: str = str(_json.get("id", "N/A"))
        self.name: str = _json.get("name", "N/A")
        self.content: str = _json.get("content", "This tag has no content.")
        self.owner: str = str(_json.get("owner_id", "N/A"))
        self.sharer: str = str(_json.get("sharer", "N/A"))
        self.nsfw: bool = _json.get("nsfw", False)
        self.restricted: bool = _json.get("restricted", False)
        self.created_at: datetime.datetime = datetime.datetime.fromisoformat(
            _json.get("created", "N/A")
        )
        self.description: str = _json.get("description", "N/A")
        self.embed: str = _json.get("embed", r"{}")
        self.location: str = str(_json.get("location_id", "N/A"))
        self.uses: str = str(_json.get("uses", "N/A"))


class TagsClient:
    """
    Tags Client
    """

    API_URL: str = "https://carl.gg/api/v1/tags/"

    def __init__(self, _loop: asyncio.AbstractEventLoop) -> None:
        """
        Construct the tag client
        """
        self.loop = _loop

    async def fetch_tag(self, _id: str) -> Tag:
        """
        Fetch a tag
        """
        response = await self.loop.run_in_executor(
            None, requests.request, "GET", f"{self.API_URL}{_id}"
        )

        _json = await self.loop.run_in_executor(None, json.loads, response.content)

        return Tag(_json)

    async def generate_image(self, tag: Tag) -> None:
        """
        Generate a pil image of a tag based on its data
        """
        


app = Flask(__name__)
loop = asyncio.get_event_loop()
tagclient = TagsClient(loop)


@app.route("/")
def main() -> None:
    """
    Main function to return "Status"
    """
    return {"Status": "Alive"}

@app.route("/get_tag/<tag_id>")
def get_tag(tag_id: str) -> None:
    """
    Main function to return "Status"
    """

    return send_file("tags/1.png")


def run() -> None:
    """
    Run the server
    """
    app.run(host="0.0.0.0", port=8080)


async def keep_alive() -> None:
    """
    Keep the server alive
    """
    while True:
        await asyncio.sleep(randint(50, 100))
        urllib.request.urlopen("http://")


Thread(target=run).start()

if sys.platform.lower() == "linux":
    Thread(target=asyncio.run, args=(keep_alive())).start()
