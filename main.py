import discord
import os
from discord.ext import commands
import requests
import json
import random
import aiosqlite
from dotenv import load_dotenv
from asyncio import sleep   # , run
from handle_database import select_value, update_value
from initialize_database import initialize_database

# import tracemalloc
# tracemalloc.start()

# -----------START UP------------ #

intents = discord.Intents.all()
print(discord.__version__)

load_dotenv()
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
hunt_code = os.environ["hunt_code"]

bot = commands.Bot(command_prefix="@ ", intents=intents)

invitations = dict()

initialize_database()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # fetch all invites from all guilds

    for guild in bot.guilds:
        invitations[str(guild.id)] = await guild.invites()
        for inv in invitations[str(guild.id)]:
            print(inv.uses)

    custom_activity = discord.Activity(type=2, name="@ help")
    await bot.change_presence(activity=custom_activity)


# -----------PHRASES---------- #

sad_words = ["zabijcie mnie", "zabijcie mn", "kill me", "killme"]

encouragements = [
    "Nie przejmuj się! Wszystko będzie dobrze", "Co się stało?",
    "Chcesz o tym porozmawiać?", "Nie mów tak! Kc <3"
]

wisdoms = [
    "`\"Ja nie mam za co przepraszać, naura\" - szm*** 2021`",
    "`\"Ty szma... szmaragdzie\" - Atencjusz`"
]

banned_nicks = [
    "!", ".", ",", "#", "?", "@", "$", "%", "^", "&", "*", " ", "[", "]", ":",
    ";"
]

# -----------VARIABLES---------- #

console_channel_id = 1403483533409783868
# whitelist_channel_id = 0000000000000000000
whitelist_channel_id = 1403734595027075133

# ------------FUNCTIONS------------ #


# fetch encouragement quote
def get_quote():
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    quote = "`\"" + json_data[0]["q"] + "\" - " + json_data[0]["a"] + "`"
    return quote


# fetch quote from "The Office"
def the_office():
    response = requests.get("https://officeapi.dev/api/quotes/random")
    json_data = json.loads(response.text)
    quote = "\"" + json_data["data"]["content"] + "\" - " + json_data["data"][
        "character"]["firstname"] + " " + json_data["data"]["character"][
            "lastname"]
    return quote


# fetch invite by invite's code
def find_invite_by_code(invite_list, code):
    for invite in invite_list:
        if invite.code == code:
            return invite


# create pie chart
def get_pie_chart(printable):
    names = [k for k, v in printable.items()]
    percentage = [v for k, v in printable.items()]

    print(names)

    quickchart_url = "https://quickchart.io/chart/create"
    post_data = {
        "chart": {
            "type": "pie",
            "data": {
                "labels": names,
                "datasets": [{
                    "data": percentage
                }]
            },
            "options": {
                "tooltips": {
                    "enabled": False
                },
                "legend": {
                    "position": "right",
                    "labels": {
                        "fontColor": "#999",
                        "fontSize": 18
                    }
                },
                "plugins": {
                    "datalabels": {
                        "align": "start",
                        "anchor": "end",
                        "clamp": True,
                        "font": {
                            "size": 16
                        },
                        "color": "black",
                    },
                    "sort": {
                        "enabled": True,
                        "mode": "array",
                        "reference": names
                    }
                }
            }
        }
    }

    response = requests.post(
        quickchart_url,
        json=post_data,
    )

    if (response.status_code != 200):
        print("Error:", response.text)
    else:
        chart_response = json.loads(response.text)
        print(chart_response["url"])
        return chart_response["url"]


async def send_activity_chart(ctx, mode):
    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            if mode == "all" or mode == "summary":
                user_activity = await select_value(cursor, 'user_activity')
                value = user_activity[str(ctx.guild.id)]
            elif mode == "channel":
                channel_activity = await select_value(cursor, 'channel_activity')
                if not ctx.message.channel_mentions[0].id:
                    channel_id = str(ctx.message.channel.id)
                else:
                    channel_id = str(ctx.message.channel_mentions[0].id)

                if channel_id not in channel_activity[str(ctx.guild.id)]:
                    await ctx.channel.send(
                        f"Nikt nie pisał na kanale {ctx.message.channel_mentions[0].mention}"
                    )
                    return
                value = channel_activity[str(ctx.guild.id)][channel_id]

    # sort members by activity
    sorted_dict = dict()
    sorted_dict = {
        k: v
        for k, v in sorted(
            value.items(), key=lambda item: item[1], reverse=True)
    }
    print(sorted_dict)
    printable = dict()
    # get num of all the messages
    all_msgs = sum(sorted_dict.values())

    if mode == "summary":
        await ctx.channel.send(f"Sumaryczna ilość wiadomości: **{all_msgs}**")
        return

    # change all activity points to percentage (only for printing)
    n = 0
    for user_key in sorted_dict:
        if n < 9 and user_key:
            print(int(user_key))
            user = await bot.fetch_user(int(user_key))
            print(user)
            if user:
                printable[str(user.name)] = round(
                    sorted_dict[str(user.id)] / all_msgs * 100, 2)
            else:
                printable[str(user_key)] = round(
                    sorted_dict[str(user_key)] / all_msgs * 100, 2)
            n += 1

    # get percentage of "other" group
    printable["inni"] = round(100 - sum(printable.values()), 2)

    # get the link of the image using custom get_pie_chart function
    link = get_pie_chart(printable)

    # send an embedded image of the pie chart
    new_embed = discord.Embed(title="**Topka atencjuszy:**", color=0xFF5733)
    new_embed.set_image(url=link)
    await ctx.channel.send(embed=new_embed)


# encourage someone if the "someone" is nice
async def encourage(message):
    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            forgave = await select_value(cursor, 'forgave')
    if message.author.id == 697503922201296956 and not forgave:
        return message.channel.send(":)")
    else:
        return message.channel.send(random.choice(encouragements))


# ------------ ON JOIN ------------ #


@bot.event
async def on_member_join(member):
    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("BEGIN TRANSACTION")
            invites = await select_value(cursor, 'invites')

            # if the guild never had any invites
            if str(member.guild.id) not in invites:
                invites[str(member.guild.id)] = dict()
                print("assigned guild to invites dict")

            await update_value(cursor, 'invites', invites)
            await conn.commit()

            # get invites' uses before join
            invites_before_join = invitations[str(member.guild.id)]

            # setup the num of invites for the guild (and later the inviter)
            await cursor.execute("BEGIN TRANSACTION")
            inviter_uses = await select_value(cursor, 'inviter_uses')
            if str(member.guild.id) not in inviter_uses:
                inviter_uses[str(member.guild.id)] = dict()
            inviter_uses_guild = inviter_uses[str(member.guild.id)]

            inv_channel = await select_value(cursor, 'inv_channel')
            inv_channel = member.guild.get_channel(inv_channel[str(member.guild.id)])

            # disabled because the admin didn't want it:
            # /-----------------------\
            # create dm channel with person who joined, if not already created
            # if not member.dm_channel:
            #   await member.create_dm()
            #   print(f"Created a DM channel with \"{member.name}\"")

            # send welcoming message if dm is possible
            # try:
            #   await member.dm_channel.send(f"Witamy w \"{member.guild.name}\"! Przeczytaj dokładnie regulamin, aby nie wpaść w kłopoty z niewiedzy. Jeżeli masz jakieś pytania lub ważną sprawę, możesz napisać do <@336475402535174154> na pw, lub napisać na kanale \"sprawa-do-administracji\". Baw się dobrze!")
            # except discord.Forbidden:
            #   print(discord.Forbidden)
            # \-----------------------/

            # fetch invites after join
            invites_after_join = await member.guild.invites()

            # fetch my profile
            # malpka = await member.guild.fetch_member(336475402535174154)

            # find the used invite
            for inv in invites_before_join:
                inv_old = find_invite_by_code(invites_after_join, inv.code)

                if not inv_old or inv.uses >= inv_old.uses:
                    continue

                print("Old invite used")
                # attach an invite to member id
                invites = await select_value(cursor, 'invites')
                invites[str(member.guild.id)][str(member.id)] = [
                    inv.code,
                    inv.inviter.name,
                    inv.inviter.id
                ]
                await update_value(cursor, 'invites', invites)

                # update invites' num of uses
                invitations[str(member.guild.id)] = invites_after_join

                if str(inv.inviter.id) not in inviter_uses_guild:
                    inviter_uses_guild[str(inv.inviter.id)] = 0
                inviter_uses_guild[str(inv.inviter.id)] += 1

                # send message on the inv channel about invite
                await inv_channel.send(f"\
                    Użytkownik {member.mention} został zaproszony kodem `{inv.code}` przez użytkownika `{inv.inviter}`. \
                    Użytkownik `{inv.inviter.name}` zaprosił już `{inviter_uses_guild[str(inv.inviter.id)]}` osób\
                ")

                # send me dm about the invite
                # await malpka.create_dm()
                # await malpka.dm_channel.send(f"\
                #     Old invite used for `{member.name}` with `{inv.code}` by `{inv.inviter}`. \
                #     It's their invitation number {inviter_uses_guild[str(inv.inviter.id)]}\
                # ")
                break
            else:
                print("Not old")

                for inv in invites_after_join:
                    if inv in invites_before_join or inv.uses <= 0:
                        continue

                    print("New invite used")

                    # attach an invite to member id
                    invites = await select_value(cursor, 'invites')
                    invites[str(member.guild.id)][str(member.id)] = [
                        inv.code,
                        inv.inviter.name,
                        inv.inviter.id
                    ]
                    await update_value(cursor, 'invites', invites)

                    # update invites' num of uses
                    invitations[str(member.guild.id)] = invites_after_join

                    if str(inv.inviter.id) not in inviter_uses_guild:
                        inviter_uses_guild[str(inv.inviter.id)] = 0
                    inviter_uses_guild[str(inv.inviter.id)] += 1

                    # send message on the inv channel about invite
                    await inv_channel.send(
                        f"Użytkownik {member.mention} został zaproszony kodem `{inv.code}` przez użytkownika `{inv.inviter}`. Użytkownik `{inv.inviter.name}` zaprosił już `{inviter_uses_guild[str(inv.inviter.id)]}` osób"
                    )

                    # send me dm about the invite
                    # await malpka.create_dm()
                    # await malpka.dm_channel.send(
                    #     f"New invite used for `{member.name}` with `{inv.code}` by `{inv.inviter}`. It's their invitation number {inviter_uses_guild[str(inv.inviter.id)]}"
                    # )
                    # break
                else:
                    print("Not new. Propably invite was single use")

                    # send message on the inv channel about invite
                    await inv_channel.send(f"\
                        Użytkownik {member.mention} został zaproszony zaproszeniem jednorazowym. \
                        Więcej info znajdziesz na \"audit log\"\
                    ")

            inviter_uses[str(member.guild.id)] = inviter_uses_guild
            await update_value(cursor, 'inviter_uses', inviter_uses)
            await conn.commit()


# ------------ ON MEMBER UPDATE ------------ #


@bot.event
async def on_member_update(before, after):
    if after.id == 833425660533014528 and after.status == discord.Status.offline and before.status != discord.Status.offline:
        await bot.get_user(336475402535174154).send("Mech bot is offline!")

    if after.bot is True:
        return

    # remove banned characters from nick
    if after.nick:
        if str(after.nick)[0] in banned_nicks:
            new_nick = after.nick
            print(f"changed from \"{new_nick}\"")
            while str(new_nick)[0] in banned_nicks:
                if len(new_nick) <= 1:
                    new_nick = after.name
                    return
                new_nick = "".join(new_nick[1:])
            print(f"to \"{new_nick}\"")
            await after.edit(nick=new_nick)

    # make appropriate nickname from a banned name
    else:
        if str(after.name)[0] in banned_nicks:
            new_nick = after.name
            print(f"changed from \"{new_nick}\"")
            while str(new_nick)[0] in banned_nicks:
                if len(new_nick) <= 1:
                    new_nick = "szma...ragd"
                    return
                new_nick = "".join(new_nick[1:])
            print(f"to \"{new_nick}\"")
            await after.edit(nick=new_nick)


# ----------- ON MESSAGE ------------ #


@bot.event
async def on_message(message):

    # do nothing if it's a bot
    if message.author.bot is True:
        return

    if message.guild:
        async with aiosqlite.connect('malpkabot.db') as conn:
            async with conn.cursor() as cursor:
                user_id = str(message.author.id)
                channel_id = str(message.channel.id)
                server_id = str(message.guild.id)

                await cursor.execute("BEGIN TRANSACTION")
                user_activity = await select_value(cursor, 'user_activity')
                channel_activity = await select_value(cursor, 'channel_activity')
                blacklist = await select_value(cursor, 'activity_blacklist')

                # create empty dict of user_activity if guild is new
                if server_id not in user_activity:
                    user_activity[server_id] = dict()
                    print(
                        f"Appended an empty dictionary for {server_id}  {message.guild.name}) to the database"
                    )

                # == PER CHANNEL ACTIVITY == #

                # new guild
                if server_id not in channel_activity:
                    channel_activity[server_id] = dict()
                    print(
                        f"Appended an empty dict for {server_id} ({message.guild.name}) to channel_activity database"
                    )

                # new channel
                if channel_id not in channel_activity[server_id]:
                    channel_activity[server_id][channel_id] = dict()
                    print(
                        f"Appended an empty dict for {channel_id} ({message.channel.name} in {message.guild.name}) to channel_activity database"
                    )

                # add per channel channel_activity point
                if user_id not in channel_activity[server_id][channel_id]:  # if new member
                    channel_activity[server_id][channel_id][user_id] = 1
                    print(f"\
                        First message for user {user_id} ({message.author.name}) \
                        in channel \"{message.channel.name}\" \
                        in guild \"{message.guild.name}\"\
                    ")
                else:
                    channel_activity[server_id][channel_id][user_id] += 1
                    print("added per channel channel_activity point")

                await update_value(cursor, 'channel_activity', channel_activity)

                # make a blacklist for new guild
                if server_id not in blacklist:
                    blacklist[server_id] = list()
                    print(f"Added new blacklist to guild \"{message.guild.name}\"")
                    await update_value(cursor, "activity_blacklist", blacklist)

                # == USER ACTIVITY == #

                # if a member wrote a msg in whitelisted channel, add 1 activity point to that member
                if channel_id not in blacklist[server_id]:
                    # if it's not member's first msg
                    if user_id in user_activity[server_id]:
                        user_activity[server_id][user_id] += 1
                        print(
                            f"Added 1 to {message.author.name} in {message.guild.name}. Now {user_activity[server_id][user_id]}"
                        )
                    else:
                        user_activity[server_id][user_id] = 1
                        print(
                            f"Added user <@{user_id}> ({message.author.name}) to {message.guild.name}'s database"
                        )

                await update_value(cursor, 'user_activity', user_activity)
                await conn.commit()

    msg = message.content

    # if msg has a sad word
    if any(word in msg.lower() for word in sad_words):
        await encourage(message)

    # if inspire command doesn't have any arguments
    if msg == "@ inspire":
        quote = get_quote()
        await message.channel.send(quote)
        return

    # if kc command has an argument
    if msg.startswith("@ kc "):
        new_mention = msg.replace("@ kc ", "")
        await message.delete()
        await message.channel.send(f"kc {new_mention} <3")
        return

    if message.channel.id == whitelist_channel_id:
        console_channel = message.guild.get_channel(console_channel_id)
        temp_msg = msg
        while "`" in temp_msg:
            temp_msg = temp_msg.replace("`")
        await console_channel.send(f"wl add {temp_msg}")
        # await console_channel.send(f"wl add {msg}")
        await message.add_reaction('✅')

    await bot.process_commands(message)


# ------------ COMMANDS ------------ #


# simple hello if member is nice
@bot.command(name="hello", brief="- przywitanie")
async def hello(ctx):
    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            forgave = await select_value(cursor, 'forgave')
    if ctx.author.id == 697503922201296956 and not forgave:
        await ctx.channel.send("BYE!")
    else:
        await ctx.channel.send("HI!")


# if in the correct channel, ping all "Bigos" members 10 times
@bot.command(name="ping", brief="- BIGOS EMERGENCY")
async def ping(ctx):
    if ctx.channel.id != 801456618734485514:
        await ctx.channel.send("Zły kanał")
        return
    if ctx.author.id == 351720708528668673:
        await ctx.channel.send("NIE")
        return
    ilość = 10
    while ilość > 0:
        await ctx.channel.send("<@&800100041972383846>")
        ilość -= 1


@bot.command(name="spam", brief="- spam")
async def spam(ctx):
    if ctx.author.id != 336475402535174154:
        await ctx.channel.send("NIE")
        return
    ilość = 10
    while ilość > 0:
        await ctx.channel.send(ctx.message.content.replace("@ spam ", ""))
        ilość -= 1


# answer kc <3 if member is nice
@bot.command(name="kc", brief="- kc <3")
async def kc(ctx):
    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            forgave = await select_value(cursor, 'forgave')
    if ctx.author.id == 697503922201296956 and not forgave:
        await ctx.channel.send(f"ja ciebie nie {ctx.author.mention}")
    else:
        await ctx.channel.send(f"kc {ctx.author.mention} <3")


# joke about banning everyone
@bot.command(name="execute", brief="- Thanos snap")
async def thanos(ctx):
    await ctx.channel.send("Ok. Banuje wszystkich z tego serwera...")
    await sleep(3)
    await ctx.channel.send("!ban @wszyscy")
    await sleep(1)
    await ctx.channel.send("Nie działa :cry:")


# if member is not nice, but asks for forgiveness, forgive them
@bot.command(name="przepraszam", brief="- przeproś bota")
async def forgive(ctx):
    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            forgave = await select_value(cursor, 'forgave')
            if ctx.author.id == 697503922201296956 and forgave is False:
                await update_value('forgave', forgave, True)
                await conn.commit()
                await ctx.channel.send("Wybaczam ci")
            else:
                await ctx.channel.send("Tobie zawsze wybaczę <3")


# send a random user created quote
@bot.command(name="mądrości", brief="- losowe cytaty od mechów")
async def wisdom(ctx):
    await ctx.channel.send(random.choice(wisdoms))


# if bot is sad, say why
@bot.command(name="czemu", brief="- spytaj się bota, czemu jest smutny")
async def sad_bot(ctx):
    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            forgave = await select_value(cursor, 'forgave')
            if forgave:
                await ctx.channel.send("Nie jestem :)")
                return
            if ctx.author.id == 697503922201296956:
                await ctx.channel.send("PRZEZ CIEBIE!")
            else:
                await ctx.channel.send("Bo Kinia jest niemiła :cry:")


# send a couple inspirational quotes
@bot.command(name="inspire", brief="- losowy cytat inspiracyjny (lub kilka)")
async def inspire(ctx, ilość):

    if not ilość.isdigit() or not 0 < int(ilość) <= 3:
        await ctx.channel.send("Ilość musi być w przedziale [1-3]")
    else:
        ilość = int(ilość)

    while ilość > 0:
        await sleep(1)
        quote = get_quote()
        await ctx.channel.send(quote)
        ilość -= 1


# send "The Office" quote
@bot.command(name="Scranton", brief="- losowy cytat z the office")
async def Scranton(ctx):
    quote = the_office()
    await ctx.channel.send(quote)


# check by who the member is invited
@bot.command(
    name="invites",
    brief="- sprawdź kto zaprosił daną osobę",
    description="Aby spingować kogoś wpisz \"<@ID>\" (zamieniając \"ID\" na ID użytkownika)"
)
async def invited_by_who(ctx, mention):
    if not ctx.message.author.guild_permissions.administrator and ctx.message.author.id != 336475402535174154:
        await ctx.channel.send("Nie masz wystarczających permisji")
        return

    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("BEGIN TRANSACTION")
            invites = await select_value(cursor, 'invites')
            str_server_id = str(ctx.message.guild.id)

            # if the guild was never checked, make an empty dict
            if str_server_id not in invites:
                invites[str_server_id] = dict()
                await update_value(cursor, 'invites', invites)
            await conn.commit()

    # fetch the user named in the command
    try:
        user_id = str(ctx.message.mentions[0].id)
    except Exception:
        user_id = str(mention)
    print(user_id)
    try:
        user_invite = invites[str_server_id][user_id]
    except KeyError:
        await ctx.channel.send("Nie znaleziono danych dla tego użytkownika")
        print(KeyError)
        return
    # answer
    try:
        await ctx.channel.send(
            f"`{ctx.message.mentions[0].name}` został zaproszony zaproszeniem `{user_invite[0]}` przez użytkownika `{user_invite[1]}`"
        )
    except Exception:
        await ctx.channel.send(
            f"`{user_id}` został zaproszony zaproszeniem `{user_invite[0]}` przez użytkownika `{user_invite[1]}`"
        )


# check top 10 active users (top 9 and "other" group)
@bot.command(
    name="activity",
    brief="- sprawdź aktywność czatowników",
    description="`@ activity <tryb> [kanał]`\nwszystkie tryby -> all, channel, blacklist, whitelist, reset\ndla \"channel\" wpisujesz ping kanału na końcu"
)
async def activity(ctx, mode, channel=None):
    if not ctx.message.author.guild_permissions.administrator and ctx.message.author.id != 336475402535174154:
        await ctx.channel.send("Nie masz wystarczających permisji")
        return

    if mode not in ("all", "channel", "reset", "blacklist", "whitelist", "summary"):
        await ctx.channel.send("Nieznana funkcja komendy `@ activity`")
        return

    if mode in ("all", "channel", "summary"):
        await send_activity_chart(ctx, mode)
        return

    if mode == "reset":
        if ctx.message.author.id != 336475402535174154:
            await ctx.channel.send("Nie masz wystarczających permisji")
            return
        async with aiosqlite.connect('malpkabot.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("BEGIN TRANSACTION")
                channel_activity = await select_value(cursor, 'channel_activity')
                channel_activity[str_server_id] = dict()
                await update_value(cursor, 'channel_activity', channel_activity)
                await conn.commit()
        print(f"reset activity for guild {ctx.guild.name}")
        await ctx.channel.send("Usunięto dane poprzedniej aktywności! (channel, nie all)")
        return

    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            str_server_id = str(ctx.guild.id)
            await cursor.execute("BEGIN TRANSACTION")
            blacklist = await select_value(cursor, 'activity_blacklist')

            if mode == "blacklist":
                channel = ctx.message.channel_mentions[0].id
                if str(channel) not in blacklist[str_server_id]:
                    blacklist[str_server_id].append(str(channel))
                    await update_value(cursor, 'activity_blacklist', blacklist)
                    await ctx.channel.send(f"Dodano kanał {ctx.guild.get_channel(channel).mention} do blacklisty")
                else:
                    await ctx.channel.send(f"Kanał {ctx.guild.get_channel(channel).mention} był już na blackliście")
                await conn.commit()
                return

            if mode == "whitelist":
                channel = ctx.message.channel_mentions[0].id
                if str(channel) in blacklist[str_server_id]:
                    blacklist[str_server_id].remove(str(channel))
                    await update_value(cursor, 'activity_blacklist', blacklist)
                    await ctx.channel.send(f"Usunięto kanał {ctx.guild.get_channel(channel).mention} z blacklisty")
                else:
                    await ctx.channel.send(f"Nie było kanału {ctx.guild.get_channel(channel).mention} na blackliście")
                await conn.commit()
                return


# reset all activity score from current guild
@bot.command(name="reset", brief="- reset activity data", hidden=True)
async def reset(ctx):
    if ctx.message.author.id != 336475402535174154:
        await ctx.channel.send("Nie masz wystarczających permisji")
        return

    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("BEGIN TRANSACTION")
            user_activity = await select_value(cursor, 'user_activity')
            del user_activity[str(ctx.guild.id)]
            await update_value(cursor, 'user_activity', user_activity)
            await conn.commit()
    print(f"reset activity for server {ctx.guild.name}")
    await ctx.channel.send("Usunięto dane poprzedniej aktywności! (all, nie channel)")


@bot.command(name="say", brief="- powiedz coś jako bot")
async def say(ctx):
    if ctx.message.author.id != 336475402535174154:
        await ctx.channel.send("Udajesz?")
        return

    if ctx.message.guild:
        await ctx.message.delete()
    says = ctx.message.content.replace("@ say ", "")
    i = 0
    try:
        while i <= int(len(says) / 15):
            await ctx.message.channel.trigger_typing()
            await sleep(1)
            i += 1
    except Exception:
        pass
    await ctx.message.channel.send(says)


@bot.command(name="EF", hidden=True)
async def EF(ctx):
    await ctx.author.create_dm()
    await ctx.author.dm_channel.send(hunt_code)


@bot.command(name="debug", hidden=True)
async def debug(ctx, db_key):
    if ctx.message.author.id != 336475402535174154:
        await ctx.channel.send("Nie masz wystarczających permisji")
        return

    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            value = await select_value(cursor, db_key)
            print(f"{db_key} – {value}")


@bot.command(
    name="invites_channel",
    brief="- ustaw kanał do pokazywania powiadomień o zaproszeniach"
)
async def invites_channel(ctx, channel=None):
    if not ctx.message.author.guild_permissions.administrator and ctx.message.author.id != 336475402535174154:
        await ctx.channel.send("Nie masz wystarczających permisji")
        return

    # set the invites channel for the appropriate guild
    channel = ctx.message.channel_mentions[0]
    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("BEGIN TRANSACTION")
            inv_channel = await select_value(cursor, 'inv_channel')
            inv_channel[str(ctx.guild.id)] = int(channel.id)
            await update_value(cursor, 'inv_channel', inv_channel)
            await conn.commit()

    await ctx.channel.send(
        f"Ustawiono kanał na zaproszenia, na {channel.mention}")


@bot.command(name="sum_invites", hidden=True)
async def sum_invites(ctx):
    # check for permission
    if ctx.message.author.id != 336475402535174154:
        await ctx.channel.send("Nie masz wystarczających permisji")
        return

    async with aiosqlite.connect('malpkabot.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("BEGIN TRANSACTION")
            inviter_uses = await select_value(cursor, 'inviter_uses')
            temp_invites = dict()

            for guild in bot.guilds:
                temp_invites[str(guild.id)] = await guild.invites()

                for inv in temp_invites[str(guild.id)]:
                    if str(guild.id) not in inviter_uses:
                        inviter_uses[str(guild.id)] = dict()
                    if str(inv.inviter.id) not in inviter_uses[str(guild.id)]:
                        inviter_uses[str(guild.id)][str(inv.inviter.id)] = 0
                    inviter_uses[str(guild.id)][str(inv.inviter.id)] += inv.uses

            await update_value(cursor, 'inviter_uses', inviter_uses)
            await conn.commit()
    await ctx.channel.send("Done")


# =====VOICE COMMANDS===== #


@bot.command(name="join", brief="- zaproś bota na kanał")
async def join_voice_channel(ctx):
    if ctx.author.voice:
        vc = ctx.message.author.voice.channel
        perms = vc.permissions_for(ctx.guild.me)

        if not perms.connect:
            await ctx.message.channel.send("Nie mogę wejść na ten kanał")
            return

        if ctx.voice_client:  # if bot in a vc
            if ctx.message.author.voice.channel == ctx.guild.voice_client.channel:  # in the same vc
                await ctx.message.channel.send("Już jestem na tym kanale")
                return

            # in a different vc
            await ctx.message.channel.send("Ktoś mnie woła. Papa")
            await sleep(2)
            await ctx.guild.voice_client.move_to(vc)

        else:  # if bot not in a vc
            await vc.connect()

        await ctx.message.channel.send("Hejka")

    else:
        await ctx.message.channel.send(
            "Musisz być na kanale, żebym mógł dołączyć")


@bot.command(name="leave", brief="- wyproś bota z kanału")
async def leave_voice_channel(ctx):

    if ctx.voice_client:  # if in a voice channel
        await ctx.message.channel.send("Papa")
        await ctx.guild.voice_client.disconnect()

    else:
        await ctx.send("Nie ma mnie na żadnym kanale")


# ------------------------------- #

bot.run(DISCORD_TOKEN)
