import discord
import requests
import datetime
import time
import threading
import asyncio

# primary thread that runs after setup
class SmashGGDonoThread(threading.Thread):
    def __init__(self, event, bot):
        self.bot = bot
        threading.Thread.__init__(self)
        self.stopped = event

    def run(self):
        # check for new donations every 10 seconds
        while not self.stopped.wait(10):
            # if new donations are found, send them to the donations channel if it's set
            for donation in self.bot.checkForNewDonations():
                if self.bot.configuration["donoChannelsID"] is not None:
                    # generate a donation embed using donation information
                    embed = self.bot.generateDonationEmbed(self.bot.smashggDonations[donation])
                    # run the send message coroutine from a non async context
                    asyncio.run_coroutine_threadsafe(self.bot.configuration["donoChannelsID"].send(embed=embed), self.bot.loop)

# class responsible for communicating with the smash.gg api
class SmashGGApiClient(): 
    SMASHGG_API_KEY = "YOUR_SMASHGG_API_KEY"

    HEADERS = {
        "Authorization": "Bearer " + SMASHGG_API_KEY
    }

    def __init__(self):
        # graphql query gets the number of pages of donations (at 50 donations per page)
        query = """
            query Shop ($slug: String) {
              shop (slug: $slug) {
                messages(query: {
                    page:1
                    perPage:50
                }) {
                  pageInfo {
                    totalPages
                  }
                }
              }
            }"""
        variables = {
            # replace slug with your shop of choice
            # example: "slug": "shop/charity-donation-2"
            "slug": "shop/your-shop-id"
        }
        url = "https://api.smash.gg/gql/alpha"
        resp = requests.post(url, headers=self.HEADERS, json={"query": query, "variables": variables})
        self.pages = resp.json()["data"]["shop"]["messages"]["pageInfo"]["totalPages"]

    def getDonations(self):
        donations = []
        # sometimes this just stops working. haven't debugged it fully yet.
        # keep an eye on the terminal and restart it if it crashes.

        # as a bit of a way to gauge how often it crashes, i had to restart
        # the bot twice during Netplay for Palestine which was about 10 hours
        # long.
        try:
            for page in range(self.pages):
                query = """
                    query Shop ($slug: String) {
                      shop (slug: $slug) {
                        messages(query: {
                            page:""" + str(page + 1) + """
                            perPage:50
                        }) {
                          pageInfo {
                            totalPages
                          }
                          nodes {
                            id
                            total
                            player {
                              user {
                                name
                                genderPronoun
                                player {
                                  gamerTag
                                }
                              }
                            }
                            message
                            gamertag
                            name
                          }
                        }
                      }
                    }"""
                variables = {
                    # replace slug with your shop of choice
                    # example: "slug": "shop/charity-donation-2"
                    "slug": "shop/your-shop-id"
                }
                url = "https://api.smash.gg/gql/alpha"
                resp = requests.post(url, headers=self.HEADERS, json={"query": query, "variables": variables})
                self.pages = resp.json()["data"]["shop"]["messages"]["pageInfo"]["totalPages"]
                donations.extend(resp.json()["data"]["shop"]["messages"]["nodes"])
            # sort all donations by id, since they don't have a timestamp exposed via the api
            donations.sort(key=lambda x:x["id"])
        except KeyError: 
            # wait until the next getDonations call to update if the returned data isn't as expected
            pass
        return donations

class DiscordBotClient(discord.Client):
    def __init__(self, campaignId):
        self.smashggAPIClient = SmashGGApiClient()
        self.smashggDonations = {}
        self.configuration = {
            "donoChannelsID": None,
        }
        self.checkForNewDonations()
        self.stopFlag = threading.Event()
        self.thread = SmashGGDonoThread(self.stopFlag, self)

        super().__init__()

    def checkForNewDonations(self):
        donations = self.smashggAPIClient.getDonations()
        newlyAdded = []
        for donation in donations:
            if donation["id"] not in self.smashggDonations:
                self.smashggDonations[donation["id"]] = donation
                newlyAdded.append(donation["id"])
        return newlyAdded

    def getMostRecentDonation(self):
        keys = list(self.smashggDonations.keys())
        keys.sort(reverse=True)
        if len(keys) <= 0: 
            return None
        return self.smashggDonations[keys[0]]

    def get10RecentDonations(self):
        keys = list(self.smashggDonations.keys())
        keys.sort(reverse=True)
        if len(keys) <= 0: 
            return []
        keys = keys[:10]
        return [self.smashggDonations[key] for key in keys]

    def getAllDonations(self):
        keys = list(self.smashggDonations.keys())
        if len(keys) <= 0:
            return []
        return [self.smashggDonations[key] for key in keys]

    # takes in a donation, title, and color
    def generateDonationEmbed(self, donation, title="New Donation!", colour=discord.Colour.from_rgb(22, 255, 22)):
        embed = discord.Embed(colour=colour)
        embed.set_author(name=title, icon_url="https://i.imgur.com/0kjbHuF.png") # smash.gg logo
        embed.set_footer(text=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " - Relay by Savestate")
        print(donation) # to console

        # here's a bit of logic to figure out what all fields are exposed in the donation
        if donation["player"] != None:
            # if the donator is a player, get player info
            if donation["player"]["user"]["player"]["gamerTag"] != None:
                # there's two spots to find the gamertag, one is in the player itself ...
                embed.add_field(name="Gamer Tag", value=donation["player"]["user"]["player"]["gamerTag"])
            elif donation["gamertag"] != None:
                # ... and the other is in the base of the donation
                embed.add_field(name="Gamer Tag", value=donation["gamertag"])

            if donation["player"]["user"]["name"] != None:
                # same deal for the name. you can find it in the player ...
                embed.add_field(name="Name", value=donation["player"]["user"]["name"])
            elif donation["name"] != None:
                # ... or in the donation itself
                embed.add_field(name="Name", value=donation["name"])

            if donation["player"]["user"]["genderPronoun"] != None:
                # if pronouns are listed, add them to the embed
                embed.add_field(name="Pronouns", value=donation["player"]["user"]["genderPronoun"])
        else:
            # if the donator isn't a player, get listed gamer tag and name if they exist
            if donation["gamertag"] != None:
                embed.add_field(name="Gamer Tag", value=donation["gamertag"])
            if donation["name"] != None:
                embed.add_field(name="Name", value=donation["name"])

        embed.add_field(name="Message", value=donation["message"] if donation["message"] else "-" )
        embed.add_field(name="Amount", value=("$%.2f"%round(donation["total"], 2)))
        return embed

    async def on_ready(self):
        # a bit of visual feedback on login
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        if message.author == self.user:
            # just in case
            return

        # commands are channel agnostic. 
        # if you want to limit scope, do so through role permissions.

        if message.content.lower() == '!list10recent':
            recentDonations = self.get10RecentDonations()
            for donation in recentDonations:
                time.sleep(1)
                await message.channel.send(embed=self.generateDonationEmbed(
                    donation, 
                    title="Repeating Donation ...", 
                    colour=discord.Colour(0xffffff))
                )

        if message.content.lower() == '!listall':
            donations = self.getAllDonations()
            await message.channel.send('LISTING ALL DONATIONS! (this might take a bit)')
            count = 1
            for donation in donations:
                time.sleep(1)
                await message.channel.send(embed=self.generateDonationEmbed(
                    donation, 
                    title=("Repeating Donation " + str(count) + "/" + str(len(donations)) + " ..."), 
                    colour=discord.Colour(0xffffff))
                )
                count += 1

        if message.content.lower() == "!help":
            await message.channel.send('!start, !stop, !setrelaychannel')

        if message.content.lower() == "!setrelaychannel":
            self.configuration["donoChannelsID"] = message.channel
            await message.channel.send('Set relay channel to #' + message.channel.name + ' `id: ' + str(message.channel.id) + "`")

        if message.content.lower() == "!start":
            self.thread.start()
            await message.channel.send('Started listening for donations')

        if message.content.lower() == "!stop":
            self.stopFlag.set()
            await message.channel.send('Stopped listening for donations')


client = DiscordBotClient(86729)
client.run('you.discord-bot.id-slash.token')