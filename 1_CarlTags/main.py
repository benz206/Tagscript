"""
If you can prove your the owner of a tag (By ID and just messaging me) I will immediately remove any associated tag that you want from me.
My purpose for this project was to expand my own knowledge and to share tags with the world.

Embed meta property preview has a max of 347 characters
string	Accepts any text without a slash (the default).
int	Accepts integers.
float	Like int but for floating point values.
path	Like string but accepts slashes.
Tag Schema
{
    _id: tag_id,
    created_at: created_at,
    guild_id: location_id,
    tag_name: name, # cut down to 20 characters max
    nsfw: true/false,
    owner_id: owner_id,
    sharer: shared_id,
    uses: int
}
"""

import asyncio
from flask import Flask
from motor.motor_asyncio import AsyncIOMotorClient
import os
import requests
from threading import Thread
import time
import urllib


connection_string = f"mongodb+srv://{os.environ['Mongo_User']}:{os.environ['Mongo_Pass']}@carltagscluster.nyxt2.mongodb.net/TagDB?retryWrites=true&w=majority"
MONGODB = AsyncIOMotorClient(connection_string)
TAGDB = MONGODB["TagDB"]["Tags"]
OAUTH2_URL = "https://discord.com/api/oauth2/authorize?client_id=929489293725040671&redirect_uri=https%3A%2F%2Fcarltags.tagscript1.repl.co%2Faccepted&response_type=code&scope=identify"


def generate_banner_url(hex_: str):
    """Generate a quick banner image so we can use it when we need it."""
    return(f"https://res.cloudinary.com/demo/image/upload/w_960,h_450,e_colorize,co_rgb:{str(hex_).replace('#', '')}/one_pixel.png")

class DuctTapeDiscord:
    """Ducttape discord client"""
    def __init__(self) -> None:
        self.api_url = "https://discord.com/api/v9"
        self.image_url = "https://cdn.discordapp.com"
        self.test_url = "https://discord.com/api/v9/users/360061101477724170"

        self.authorization = {
            "Authorization": f'Bot {os.environ["TOKEN"]}'
        }
    
    def get_user_info(self, user_id: int) -> dict:
        """Get a users info through our very shitty client"""
        user = requests.get(self.api_url + f"/users/{str(user_id)}", headers=self.authorization)
        return user.json()

    def generate_user_avatar(self, user_id: str, hash_: str) -> str:
        """Generate a users avatar based on a hash and id"""
        return(f"{self.image_url}/avatars/{str(user_id)}/{str(hash_)}.png")


client = DuctTapeDiscord()


class MetaEmbed:
    """
    A class for creating embeds through meta tags
    """
    def __init__(self) -> None:
        pass

    def generate_embed(
            self, 
            title: str = None,
            title_url: str = None,
            author_name: str = None,
            thumbnail: str = None,
            color: str = None,
            description: str = None,
            
        ):
        """Generate an embed based on the given perms"""
        embed = '<meta property="og:type" content="Site Content" />'

        if title:
            embed += f'\n<meta property="og:title" content="{title}" />'
        if title_url:
            embed += f'\n<meta property="og:url" content="{title_url}" />'
        if author_name:
            embed += f'\n<meta property="og:site_name" content="{author_name}">'
        if thumbnail:
            embed += f'\n<meta property="og:image" content="{thumbnail}" />'
        if color:
            if str(color).strip() == "000000":
                color = "000001"
            embed += f'\n<meta name="theme-color" content="#{color}">'
        if description:
            embed += f'\n<meta property="og:description" content="{description}" />'
        print(embed)
        return embed

meta_embed = MetaEmbed()


app = Flask(__name__)
@app.route("/")	
def home():
	return {"status": "Alive"}

@app.route("/help/<int:unix>")
def help_route(unix):
    return '''
        <meta property="og:title" content="carltags help" />
        <meta property="og:site_name" content="Website Name">
        <meta property="og:url" content="http://google.com/" />
        <meta property="og:image" content="https://i.imgur.com/PllK6g6.png" />
        <meta property="og:description" content="Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, sssssss" />
        <meta name="theme-color" content="#7289DA">
        '''

"""
<meta property="og:title" content="sus - 715929" />
<meta property="og:url" content="https://carl.gg/api/v1/tags/715929" />
<meta property="og:site_name" content="_Leg3ndary#5759">
<meta property="og:image" content="https://cdn.discordapp.com/avatars/360061101477724170/63254ba6f48379de1660e403356f1e76.png" />
<meta property="twitter:card" content="https://res.cloudinary.com/demo/image/upload/w_960,h_450,e_colorize,co_rgb:#000000/one_pixel.png" />
<meta name="theme-color" content="#000000">
<meta property="og:description" content="pretend stuff is actually here" />"""

@app.route("/accepted")
def accepted_oath_route():
    """Just return a success"""
    return '''
    <h1>Success!</h1>
    <p>Thank you for accepting, you should now see your info appear on tags you own!
    You can now close this page!</p>
    '''

@app.route("/tag/info/<int:tag_id>/<int:time>")
def tag_info_tagid(tag_id, time):
    """Return a meta embed with a tags info"""

@app.route("/test_endpoint/<unix>")
def test_endpoint(unix):
    """thingy"""
    info = client.get_user_info(360061101477724170)
    avatar = client.generate_user_avatar(info.get("id"), info.get("avatar"))
    print(avatar)

    embed = meta_embed.generate_embed(
        "sus - #715929",
        "https://carl.gg/t/715929",
        f'{info.get("username")}#{info.get("discriminator")} - {info.get("id")}',
        avatar,

        info.get("banner_color").replace("#", ""),
        """Created at Tue, 30 Mar 2021 16:16:37 GMT
        nsfw: False
        Shared by: name of person who shared
        Uses: 2
        Guild Id: 680224122244038731
        """
    )
    return embed

def run():
    app.run(host="0.0.0.0", port=8080)

server = Thread(target=run)
server.start()

async def keep_alive():
    while 1:
        urllib.request.urlopen("https://CarlTags.tagscript1.repl.co")
        await asyncio.sleep(200)

keep_alive()
