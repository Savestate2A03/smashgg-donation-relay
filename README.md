# smash.gg Donation Relay Bot

## Overview 
This python script was made to pull donations regularly (every 10 seconds) from a smash.gg charity shop and relay them to a specified Discord channel of a server the bot resided in. It's since been genericified (API keys replaced, urls changed) so you can change it according to your needs. 

## Setup
The smash.gg donation relay bot relys on the two packages `discord` and `requests` which can both be installed with `pip`. After installing those, add in your API keys and bot information from the **Drop-in replacements** section below. From there, just run the bot using python, run `!setrelaychannel` in the channel where you want donations to be relayed, and then run `!start` to start listening for new donations. 

## Drop-in replacements
There's a few spots where you'll need to add your info for the bot to work properly:
 * `SMASHGG_API_KEY = "YOUR_SMASHGG_API_KEY"`
 * `client.run('you.discord-bot.id-slash.token')`
 * `"slug": "shop/your-shop-id"` (in two spots)

## Commands
 * `!setrelaychannel` This command sets the channel where donation embeds will be generated; run it in your channel of choice
 * `!start` Starts listening for new donations, which will be relayed in the set channel from `!setrelaychannel`
 * `!stop` Stops listening for new donations
 * `!listall` Lists every single donation
 * `!list10recent` Lists the 10 most recent donations

## Screenshots
Setting a relay channel, start listening for donations, and listing all the donations

![Setting a relay channel, start listening for donations, and listing all the donations](https://i.imgur.com/Odm0zsq.png)

A live donation relayed to Discord

![A live donation relayed to Discord](https://i.imgur.com/bSBXdwy.png)

An anonymous donation relayed to Discord

![An anonymous donation relayed to Discord](https://i.imgur.com/FyUrvlF.png)

## Warnings
I believe I have most or all of the potential crash bugs fixed, but just in case, keep an eye on the terminal it's running in. Monitor it and look out for a stack trace printed to the console and restart the program if one does get printed. (remember to `!setrelaychannel` and `!start`)
