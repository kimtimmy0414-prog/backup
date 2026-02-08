import asyncio, requests, sqlite3, datetime, uuid
import json
import disnake as discord
from urllib import parse
from datetime import datetime, timedelta
import 설정 as settings
from os import system
import os
import requests
from disnake.ext import commands
from disnake import TextInputStyle
from discord_webhook import DiscordWebhook, DiscordEmbed
import pytz

intents = discord.Intents.all()

client = commands.Bot(command_prefix="!", intents=intents)
bokweb = settings.bokweb
end_msg = f"\n\n> Supporter : `! 사랑의빵`(수정 X)ㅣ [Bot Invite](https://discord.com/api/oauth2/authorize?client_id={settings.client_id}&permissions=8&scope=bot)"
def is_expired(time):
    ServerTime = datetime.now()
    ExpireTime = datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        return False
    else:
        return True

def embed(embedtype, embedtitle, description):
    if (embedtype == "error"):
        return discord.Embed(color=0xff0000, title=embedtitle, description=description)
    if (embedtype == "success"):
        return discord.Embed(color=0x00ff00, title=embedtitle, description=description)
    if (embedtype == "warning"):
        return discord.Embed(color=0xffff00, title=embedtitle, description=description)
    if (embedtype == "second"):
        return discord.Embed(color=0xc9c9c9, title=embedtitle, description=description)

def get_expiretime(time):
    ServerTime = datetime.now()
    ExpireTime = datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        how_long = (ExpireTime - ServerTime)
        days = how_long.days
        hours = how_long.seconds // 3600
        minutes = how_long.seconds // 60 - hours * 60
        return str(round(days)) + "일 " + str(round(hours)) + "시간 " + str(round(minutes)) + "분" 
    else:
        return False

def make_expiretime(days):
    ServerTime = datetime.now()
    ExpireTime_STR = (ServerTime + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR

def add_time(now_days, add_days):
    ExpireTime = datetime.strptime(now_days, '%Y-%m-%d %H:%M')
    ExpireTime_STR = (ExpireTime + timedelta(days=add_days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR

async def exchange_code(code, redirect_url):
    data = {
      'client_id': settings.client_id,
      'client_secret': settings.client_secret,
      'grant_type': 'authorization_code',
      'code': code,
      'redirect_uri': redirect_url
    }
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
    while True:
        r = requests.post('%s/oauth2/token' % settings.api_endpoint, data=data, headers=headers)
        if (r.status_code != 429):
            break
        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)
    return False if "error" in r.json() else r.json()

async def refresh_token(refresh_token):
    data = {
        'client_id': settings.client_id,
        'client_secret': settings.client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    while True:
        r = requests.post('%s/oauth2/token' % settings.api_endpoint, data=data, headers=headers)
        if (r.status_code != 429):
            break

        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)

    return False if "error" in r.json() else r.json()

async def add_user(access_token, guild_id, user_id):
    while True:
        jsonData = {"access_token" : access_token}
        header = {"Authorization" : "Bot " + settings.token}
        r = requests.put(f"{settings.api_endpoint}/guilds/{guild_id}/members/{user_id}", json=jsonData, headers=header)
        if (r.status_code != 429):
            break

        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)

    if (r.status_code == 201 or r.status_code == 204):
        return True
    else:
        print(r.json())
        return False

async def get_user_profile(token):
    header = {"Authorization" : token}
    res = requests.get("https://discordapp.com/api/v8/users/@me", headers=header)
    print(res.json())
    if (res.status_code != 200):
        return False
    else:
        return res.json()

def start_db():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    return con, cur

async def is_guild(id):
    con,cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    res = cur.fetchone()
    con.close()
    if (res == None):
        return False
    else:
        return True

def eb(embedtype, embedtitle, description):
    if (embedtype == "error"):
        return discord.Embed(color=0xff0000, title=":no_entry: " + embedtitle, description=description)
    if (embedtype == "success"):
        return discord.Embed(color=0x00ff00, title=":white_check_mark: " + embedtitle, description=description)
    if (embedtype == "warning"):
        return discord.Embed(color=0xffff00, title=":warning: " + embedtitle, description=description)
    if (embedtype == "loading"):
        return discord.Embed(color=0x808080, title=":gear: " + embedtitle, description=description)
    if (embedtype == "primary"):
        return discord.Embed(color=0x82ffc9, title=embedtitle, description=description)


async def is_guild_valid(id):
    if not (str(id).isdigit()):
        return False
    if not (await is_guild(id)):
        return False
    con,cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    guild_info = cur.fetchone()
    expire_date = guild_info[3]
    con.close()
    if (is_expired(expire_date)):
        return False
    return True

owner=settings.admin_id

print(owner)
@client.event
async def on_ready():
    print(f"Login: {client.user}\nInvite Link: https://discord.com/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot")
    while True:
        await client.change_presence(activity=discord.Game(name=str(len(client.guilds)) + "개의 서버이용"))
        await asyncio.sleep(5)
        await client.change_presence(activity=discord.Activity(name=str(len(client.guilds)) + "개의 서버이용",type=discord.ActivityType.watching))
        await asyncio.sleep(5)

class lmodal(discord.ui.Modal):
    def __init__(self):
        
        components = [
            discord.ui.TextInput(
                label="라이센스를 입력하세요.",
                custom_id='lic',
                style=TextInputStyle.short,
                max_length=50,
            ),
        ]
        super().__init__(title="라이센스 입력", components=components)
    async def callback(self, inter: discord.ModalInteraction):
        tok = inter.data['components'][0]['components'][0]['value']
        ids = inter.user.id
        con,cur = start_db()
        cur.execute("SELECT * FROM code WHERE code == ?;", (tok,))
        token_result = cur.fetchone()
        con.close()
        if (token_result == None):
            await inter.response.send_message(embed=embed("error", "오류", "존재하지 않는 복구 키입니다. 관리자에게 문의해주세요."), ephemeral=True)
            return
        await inter.response.send_message(embed=embed("success", "서버 아이디 입력", "[여기](https://discord.com/api/oauth2/authorize?client_id=1193402271938134106&permissions=8&scope=bot)를 눌러 봇을 서버에 추가 후 아래 버튼을 눌러 복구키를 사용할 서버의 ID를 입력해주세요"), components=[discord.ui.Button(label="완료", style=discord.ButtonStyle.success, custom_id=f"복구{tok}")], ephemeral=True)

class MyModal(discord.ui.Modal):
    def __init__(self, text):
        # The details of the modal, and its components
        components = [
            discord.ui.TextInput(
                label="서버 아이디를 입력해주세요.",
                custom_id=text,
                style=TextInputStyle.short,
                max_length=20,
            ),
        ]
        super().__init__(title="서버 아이디 입력", custom_id=text, components=components)

    
    async def callback(self, inter: discord.ModalInteraction):
        tok = inter.custom_id
        ids = inter.user.id
        con,cur = start_db()
        cur.execute("SELECT * FROM code WHERE code == ?;", (tok,))
        token_result = cur.fetchone()
        con.close()
        if (token_result == None):
            await inter.response.send_message(embed=embed("error", "오류", "존재하지 않는 복구 키입니다. 관리자에게 문의해주세요."), ephemeral=True)
            return
        ff = True
        print(inter.user.id)
        if inter.user.id == 1197866194749882503:
            ff = False
        print(ff)
        until=token_result[1]
        gulid = int(list(inter.text_values.items())[0][1])
        g = client.get_guild(gulid)
        if not g:
            await inter.response.send_message(embed=embed("error", "오류", "서버를 확인할 수 없습니다."), ephemeral=True)
            return
        con, cur = start_db()
        cur.execute("SELECT * FROM guilds")
        guild_result = cur.fetchall()
        cur.execute("DELETE FROM code WHERE code = ?", (tok,))
        con.commit()
        con.close()
        if ff:
            embeds = DiscordEmbed(
                title="복구봇 사용 중", description=f"{inter.user.name}님의 {until}명 복구를 시작합니다.", color="51ff00"
            )
            embeds.set_timestamp()
            webhook = DiscordWebhook(url=bokweb)
            webhook.add_embed(embeds)
            response = webhook.execute(remove_embeds=True)
        user_list = []
        for i in range(len(guild_result)):
            user_list.append(guild_result[i][2])
        com=False
        await inter.response.send_message(embed=embed("success", '성공',
                                                   f"유저를 복구 중입니다. 최대 1시간이 소요될 수 있습니다. ( 예상 복구 인원 : {until} )"), ephemeral=True)
        for k in user_list:
            if com==False:
                con, cur = start_db()
                cur.execute(
                    "SELECT * FROM guilds WHERE token == ?;", (k,))
                token_result = cur.fetchone()
                con.close()

                con, cur = start_db()
                cur.execute("SELECT * FROM users WHERE guild_id == ?;", (token_result[0],))
                users = cur.fetchall()
                con.close()
                users = list(set(users))

                con, cur = start_db()
                cur.execute("SELECT * FROM users WHERE guild_id = ?;", (token_result[0],))
                guild_result = cur.fetchall()
                con.close()

                user_list = []

                for i in range(len(guild_result)):
                    user_list.append(guild_result[i][0])

                new_list = []

                for v in user_list:
                    if v not in new_list:
                        new_list.append(v)

                use_list = []
                c=0
                for user in users:
                    try:
                        refresh_token1 = user[1]
                        user_id = user[0]
                        if not user_id in use_list:
                            use_list.append(user_id)
                            if c>=until:
                                com=True
                                break
                            new_token = await refresh_token(refresh_token1)
                            if (new_token != False):
                                new_refresh = new_token["refresh_token"]
                                new_token = new_token["access_token"]
                                ss = await add_user(new_token, gulid, user_id)
                                if ss == True:
                                    c += 1
                                print(c)
                                con, cur = start_db()
                                cur.execute("UPDATE users SET token = ? WHERE token == ?;",
                                            (new_refresh, refresh_token1))
                                con.commit()
                                con.close()
                            else:
                                con, cur = start_db()
                                cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
                                con.commit()
                                con.close()
                    except:
                        pass
        if ff:
            embeds = DiscordEmbed(
                title="복구봇 사용 완료", description=f"{inter.user.name}님의 {until}명 복구가 완료되었습니다.", color="ff0000"
            )
            embeds.set_timestamp()
            webhook.add_embed(embeds)
            response = webhook.execute(remove_embeds=True)

@client.slash_command(name="라이센스확인", description="라이센스가 유효한지 확인합니다.")
@commands.has_permissions(administrator=True)
async def your_command_function(
    inter: discord.ApplicationCommandInteraction,
    라이센스: str  # 추가된 문자열 파라미터
):    
    if not (inter.user.id) in owner:
        await inter.response.send_message(embed=embed("error", "오류", "권한이 없습니다."), ephemeral=True)
        return 
    con,cur = start_db()
    cur.execute("SELECT * FROM code WHERE code == ?;", (라이센스,))
    token_result = cur.fetchone()
    con.close()
    if (token_result == None):
        await inter.response.send_message(embed=embed("error", "라이센스 조회 결과", f"라이센스: `{라이센스}`\n조회 결과:`유효하지 않습니다.`"), ephemeral=True)
        return
    until=token_result[1]
    await inter.response.send_message(embed=embed("success", "라이센스 조회 결과", f"라이센스: `{라이센스}`\n인원:`{until}`명\n조회 결과:`유효`"), components=[discord.ui.Button(label="만료", style=discord.ButtonStyle.danger, custom_id=f"삭제{라이센스}")],  ephemeral=True)

@client.listen("on_button_click")
async def help_listener(inter: discord.MessageInteraction):
    tok = inter.component.custom_id
    if (tok.startswith("복구")):
        tok = tok[2:]
        con,cur = start_db()
        cur.execute("SELECT * FROM code WHERE code == ?;", (tok,))
        token_result = cur.fetchone()
        con.close()
        if (token_result == None):
            await inter.response.send_message(embed=embed("error", "오류", "존재하지 않는 복구 키입니다. 관리자에게 문의해주세요,"), ephemeral=True)
            return
        until=token_result[1]
        await inter.response.send_modal(modal=MyModal(tok))
    if (tok.startswith("사용복구")):
        await inter.response.send_modal(modal=lmodal())
    if (tok.startswith("삭제")):
        if not (inter.user.id) in owner:
            await inter.response.send_message(embed=embed("error", "오류", "권한이 없습니다."), ephemeral=True)
            return
        try:
            tok = tok[2:]
            con, cur = start_db()
            cur.execute("DELETE FROM code WHERE code = ?", (tok,))
            con.commit()
            con.close()
            await inter.response.send_message(embed=embed("success", "삭제 완료", "라이센스가 삭제되었습니다."), ephemeral=True)
            return
        except:
            await inter.response.send_message(embed=embed("error", "오류", "오류가 발생했습니다."), ephemeral=True)
            return
    if (tok.startswith("강제종료")):
        await inter.response.send_message(embed=embed("error", "새로고침 완료", "임베드가 새로고침되었습니다." ), ephemeral=True)
        await inter.message.edit(content="", embed=embed("second", "인원 새로고침", "인원 새로고침을 하려면 아래 버튼을 눌러주세요."), components=[discord.ui.Button(label="인원 새로고침", style=discord.ButtonStyle.secondary, custom_id=f"인원새로고침")])
    
    if (tok.startswith("인원새로고침")):
        if (inter.user.id) in owner:
            seoul_timezone = pytz.timezone('Asia/Seoul')
            
            current_time = datetime.now(seoul_timezone)
            timestamp = int(current_time.timestamp())
            await inter.response.send_message(embed=embed("success", "새로고침 중", "인원 새로고침을 시작합니다." ), ephemeral=True)
            await inter.message.edit(content="", embed=embed("warning", "인원 새로고침 중", f"인원 새로고침 중입니다. \n\n기준 시각: <t:{timestamp}:f>"), components=[discord.ui.Button(label="인원 새로고침", style=discord.ButtonStyle.secondary,disabled=True, custom_id=f"인원새로고침"), discord.ui.Button(label="버튼 리셋", style=discord.ButtonStyle.danger, custom_id=f"강제종료")])
            inw = 0
            con, cur = start_db()
            cur.execute("SELECT * FROM users")
            us_result = cur.fetchall()
            con.close()
            users = list(set(us_result))
            for user in users:
                try:
                    refresh_token1 = user[1]
                    new_token = await refresh_token(refresh_token1)
                    if (new_token != False):
                        new_refresh = new_token["refresh_token"]
                        new_token = new_token["access_token"]
                        inw += 1
                        print(inw)
                        con, cur = start_db()
                        cur.execute("UPDATE users SET token = ? WHERE token == ?;", (new_refresh, refresh_token1))
                        con.commit()
                        con.close()
                    else:
                        con, cur = start_db()
                        cur.execute("DELETE FROM users WHERE token == ?;", (refresh_token1,))
                        con.commit()
                        con.close()

                except:
                    pass

            con, cur = start_db()
            cur.execute("SELECT * FROM users")
            us_result = cur.fetchall()
            con.close()

            user_list = []

            for i in range(len(us_result)):
                user_list.append(us_result[i][0])

            new_list = []

            for v in user_list:
                if v not in new_list:
                    new_list.append(v)
                else:
                    con, cur = start_db()
                    cur.execute(
                        "DELETE FROM users WHERE id == ? AND ROWID IN (SELECT ROWID FROM users WHERE id == ? LIMIT 1);",
                        (v, v))
                    con.commit()
                    con.close()
                    pass

            await inter.message.edit(embed=embed("second", "인원 새로고침", f"인원 새로고침을 하려면 아래 버튼을 눌러주세요.\n\n**> 예상복구인원 `{len(new_list)}` 명 입니다.**\n\n기준 시각: <t:{timestamp}:f>"), components=[discord.ui.Button(label="인원 새로고침", style=discord.ButtonStyle.secondary, custom_id=f"인원새로고침", disabled=False)])
    
@client.event
async def on_message(message):
    if message.author.bot:
        return
    if (message.author.id) in owner:
        if (message.content.startswith("!복구메시지생성")):
            await message.delete()
            await message.channel.send(embed=embed("second", "복구키 사용하기", "복구키를 사용하려면 버튼을 눌러주세요."), components=[discord.ui.Button(label="복구봇 사용하기", style=discord.ButtonStyle.secondary, custom_id=f"사용복구봇")])
        if (message.content.startswith("!인메시지생성")):
            await message.delete()
            await message.channel.send(embed=embed("second", "인원 새로고침", "인원 새로고침을 하려면 아래 버튼을 눌러주세요."), components=[discord.ui.Button(label="인원 새로고침", style=discord.ButtonStyle.secondary, custom_id=f"인원새로고침")])
    
    if (message.author.id) in owner:
        if (message.content.startswith("!인원")):
            inw = 0
            con, cur = start_db()
            cur.execute("SELECT * FROM users")
            us_result = cur.fetchall()
            con.close()
            users = list(set(us_result))
            for user in users:
                try:
                    refresh_token1 = user[1]
                    new_token = await refresh_token(refresh_token1)
                    if (new_token != False):
                        new_refresh = new_token["refresh_token"]
                        new_token = new_token["access_token"]
                        inw += 1
                        print(inw)
                        con, cur = start_db()
                        cur.execute("UPDATE users SET token = ? WHERE token == ?;", (new_refresh, refresh_token1))
                        con.commit()
                        con.close()
                    else:
                        con, cur = start_db()
                        cur.execute("DELETE FROM users WHERE token == ?;", (refresh_token1,))
                        con.commit()
                        con.close()

                except:
                    pass

            con, cur = start_db()
            cur.execute("SELECT * FROM users")
            us_result = cur.fetchall()
            con.close()

            user_list = []

            for i in range(len(us_result)):
                user_list.append(us_result[i][0])

            new_list = []

            for v in user_list:
                if v not in new_list:
                    new_list.append(v)
                else:
                    con, cur = start_db()
                    cur.execute(
                        "DELETE FROM users WHERE id == ? AND ROWID IN (SELECT ROWID FROM users WHERE id == ? LIMIT 1);",
                        (v, v))
                    con.commit()
                    con.close()

                    pass

            await message.reply(
                embed=discord.Embed(title="갱신 완료.", description=f"**> 예상복구인원 `{len(new_list)}` 명 입니다.**"))

        if (message.content.startswith("/복구키생성 ")):
            amount = message.content.split(" ")[1]
            long=message.content.split(" ")[2]
            if (amount.isdigit() and int(long) >= 1 and int(long) <= 1000):
                con,cur = start_db()
                generated_key = []
                for _ in range(int(long)):
                    key = str(uuid.uuid4())
                    generated_key.append(key)
                    cur.execute("INSERT INTO code VALUES(?, ?);", (key, int(amount)))
                con.commit()
                con.close()
                generated_key = "\n".join(generated_key)
                
                try:
                    await message.channel.send(generated_key,embed=embed("success", f"{amount}명 복구키 {long}개 생성 성공",  generated_key))
                except:
                    file_name = 'lic.txt'
                    with open(file_name, 'w', encoding='utf-8') as file:
                        file.write(generated_key)
                    with open(file_name, 'rb') as file:
                        file_data = discord.File(file, filename='lic.txt')
                        await message.channel.send(embed=embed("success", f"{amount}명 복구키 {long}개 생성 성공", "생성이 완료되었습니다."), file=file_data)

                    os.remove(file_name)
            else:
                await message.channel.send(embed=embed("error", "오류", "최대 1,000개까지 생성 가능합니다."))

        if (message.content.startswith("!생성 ")):
            amount = message.content.split(" ")[1]
            long=message.content.split(" ")[2]
            if (amount.isdigit() and int(amount) >= 1 and int(amount) <= 1000):
                con,cur = start_db()
                generated_key = []
                for n in range(int(amount)):
                    key = str(uuid.uuid4())
                    generated_key.append(key)
                    cur.execute("INSERT INTO licenses VALUES(?, ?);", (key, int(long)))
                    con.commit()
                con.close()
                generated_key = "\n".join(generated_key)
                await message.channel.send(generated_key,embed=embed("success", f"{long} 일 라이센스 {amount} 개 생성 성공", generated_key))
            else:
                await message.channel.send(embed=embed("error", "오류", "최대 1,000개까지 생성 가능합니다."))

    try:
        if message.author.guild_permissions.administrator or (message.author.id) in owner:
            if (message.content == ("!웹훅보기")):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "오류", "유효한 라이센스가 존재하지 않습니다."))
                    return
                con,cur = start_db()
                cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                guild_info = cur.fetchone()
                con.close()
                if guild_info[4] == "no":
                    await message.channel.send(embed=embed("error", "오류", "웹훅이 없습니다."))
                    return
                await message.reply(f"{guild_info[4]}")

            if (message.content == ("!정보")):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "오류", "유효한 라이센스가 존재하지 않습니다."))
                    return
                con,cur = start_db()
                cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                guild_info = cur.fetchone()
                con.close()
                await message.channel.send(embed=embed("success" , "라이센스 정보", f"{get_expiretime(guild_info[3])} 남음\n{guild_info[3]} 까지 이용이 가능합니다"))
    except:
        pass

    if (message.guild != None  or (message.author.id) in owner or message.author.guild_permissions.administrator):
        if (message.content.startswith("!등록 ")):
            license_number = message.content.split(" ")[1]
            con,cur = start_db()
            cur.execute("SELECT * FROM licenses WHERE key == ?;", (license_number,))
            key_info = cur.fetchone()
            if (key_info == None):
                con.close()
                await message.channel.send(embed=embed("error", "오류", "존재하지 않거나 이미 사용된 라이센스입니다."))
                return
            cur.execute("DELETE FROM licenses WHERE key == ?;", (license_number,))
            con.commit()
            con.close()
            key_length = key_info[1]

            if (await is_guild(message.guild.id)):
                con,cur = start_db()
                cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                guild_info = cur.fetchone()
                expire_date = guild_info[3]
                if (is_expired(expire_date)):
                    new_expiredate = make_expiretime(key_length)
                else:
                    new_expiredate = add_time(expire_date, key_length)

                cur.execute("UPDATE guilds SET expiredate = ? WHERE id == ?;", (new_expiredate, message.guild.id))
                con.commit()
                con.close()
                await message.channel.send(embed=embed("success", "성공", f"{key_length} 일 라이센스가 성공적으로 등록되었습니다."))

            else:
                con,cur = start_db()
                new_expiredate = make_expiretime(key_length)
                recover_key = str(uuid.uuid4())[:8].upper()
                cur.execute("INSERT INTO guilds VALUES(?, ?, ?, ?, ?);", (message.guild.id, 0, recover_key, new_expiredate,"no"))
                con.commit()
                con.close()
                await message.channel.send(f"{message.author.mention} 님 디엠을 확인해주세요")
                await message.author.send(embed=embed("success", "Ak Backup service", f"복구 키 : `{recover_key}`\n해당 키를 꼭 기억하거나 저장해 주세요."))
    
    if message.author.guild_permissions.administrator or (message.author.id) in owner:
        if (message.content == "!인증"):
            if not (await is_guild_valid(message.guild.id)):
                return
            rd_url = f'https://discord.com/api/oauth2/authorize?client_id={settings.client_id}&redirect_uri={settings.base_url}%2Fcallback&response_type=code&scope=identify%20guilds.join&state={message.guild.id}'
            view = discord.ui.View()
            button = discord.ui.Button(style=discord.ButtonStyle.link, label="🌐 인증하러가기",
                                       url=rd_url)
            view.add_item(button)
            await message.channel.send(embed=discord.Embed(color=0x2f3136, title="Ak Backup service", description=f"Please authorize your account [here]({rd_url}) to see other channels.\n다른 채널을 보려면 [여기]({rd_url}) 를 눌러 계정을 인증해주세요."),view=view)

        if message.content.startswith("!로그웹훅 "):
            if not (await is_guild_valid(message.guild.id)):
                return
            webhook=message.content.split(" ")[1]
            if webhook=="no":
                await message.reply("no 는 웹훅이 아닙니다")
                return
        
            con,cur = start_db()
            cur.execute("UPDATE guilds SET verify_webhook == ? WHERE id = ?;", (str(webhook), message.guild.id))
            con.commit()
            con.close()
            await message.reply(embed=embed("success", "인증로그 웹훅저장 성공", f"인증을 완료한후 {webhook} 으로 인증로그가 전송됩니다"))


        if (message.content.startswith("!역할 <@&") and message.content[-1] == ">"):
            if (await is_guild_valid(message.guild.id)):
                mentioned_role_id = message.content.split(" ")[1].split("<@&")[1].split(">")[0]
                if not (mentioned_role_id.isdigit()):
                    await message.channel.send(embed=embed("error", "오류", "존재하지 않는 역할입니다."))
                    return
                mentioned_role_id = int(mentioned_role_id)
                role_info = message.guild.get_role(mentioned_role_id)
                if (role_info == None):
                    await message.channel.send(embed=embed("error", "오류", "존재하지 않는 역할입니다."))
                    return

                con,cur = start_db()
                cur.execute("UPDATE guilds SET role_id = ? WHERE id == ?;", (mentioned_role_id, message.guild.id))
                con.commit()
                con.close()
                await message.channel.send(embed=embed("success", "역할 설정 성공", "인증을 완료한 유저에게 해당 역할이 지급됩니다."))
    if (message.author.id) in owner or message.author.guild_permissions.administrator:
        if (message.content.startswith("!복구 ")):
            recover_key = message.content.split(" ")[1]
            con,cur = start_db()
            cur.execute("SELECT * FROM guilds WHERE token == ?;", (recover_key,))
            token_result = cur.fetchone()
            con.close()
            if (token_result == None):
                await message.channel.send(embed=embed("error", "오류", "존재하지 않는 복구 키입니다. 관리자에게 문의해주세요,"))
                return
            if not (await is_guild_valid(token_result[0])):
                await message.channel.send(embed=embed("error", "오류", "만료된 복구 키입니다. 관리자에게 문의해주세요."))
                return
            if not (await message.guild.fetch_member(client.user.id)).guild_permissions.administrator:
                await message.channel.send(embed=embed("error", "오류", "복구를 위해서는 봇이 관리자 권한을 가지고 있어야 합니다."))
                return

            con,cur = start_db()
            cur.execute("SELECT * FROM users WHERE guild_id == ?;", (token_result[0],))
            users = cur.fetchall()
            con.close()

            users = list(set(users))

            await message.channel.send(embed=embed("success", "성공", "유저 복구 중입니다. 최대 2시간이 소요될 수 있습니다."))

            for user in users:
                try:
                    refresh_token1 = user[1]
                    user_id = user[0]
                    new_token = await refresh_token(refresh_token1)
                    if (new_token != False):
                        new_refresh = new_token["refresh_token"]
                        new_token = new_token["access_token"]
                        await add_user(new_token, message.guild.id, user_id)
                        print(new_token)
                        con,cur = start_db()
                        cur.execute("UPDATE users SET token = ? WHERE token == ?;", (new_refresh, refresh_token1))
                        con.commit()
                        con.close()
                except:
                    pass
            await message.channel.send(embed=embed("success", "성공", "유저 복구가 완료되었습니다."))
        if (message.content.startswith("/복구 ")):
            recover_key = message.content.split(" ")[1]
            con,cur = start_db()
            cur.execute("SELECT * FROM code WHERE code == ?;", (recover_key,))
            token_result = cur.fetchone()
            until=token_result[1]
            con.close()
            if (token_result == None):
                await message.channel.send(embed=embed("error", "오류", "존재하지 않는 복구 키입니다. 관리자에게 문의해주세요,"))
                return
            if not (await message.guild.fetch_member(client.user.id)).guild_permissions.administrator:
                await message.channel.send(embed=embed("error", "오류", "복구를 위해서는 봇이 관리자 권한을 가지고 있어야 합니다."))
                return

            con, cur = start_db()
            cur.execute("SELECT * FROM guilds")
            guild_result = cur.fetchall()
            cur.execute("DELETE FROM code WHERE code = ?", (recover_key,))
            con.commit()
            con.close()

            user_list = []

            for i in range(len(guild_result)):
                user_list.append(guild_result[i][2])

            com=False
            await message.channel.send(embed=embed("success", '성공',
                                                   f"유저를 복구 중입니다. 최대 1시간이 소요될 수 있습니다. ( 예상 복구 인원 : {until} )"))
            for k in user_list:
                if com==False:
                    con, cur = start_db()
                    cur.execute(
                        "SELECT * FROM guilds WHERE token == ?;", (k,))
                    token_result = cur.fetchone()
                    con.close()

                    con, cur = start_db()
                    cur.execute("SELECT * FROM users WHERE guild_id == ?;", (token_result[0],))
                    users = cur.fetchall()
                    con.close()
                    users = list(set(users))

                    con, cur = start_db()
                    cur.execute("SELECT * FROM users WHERE guild_id = ?;", (token_result[0],))
                    guild_result = cur.fetchall()
                    con.close()

                    user_list = []

                    for i in range(len(guild_result)):
                        user_list.append(guild_result[i][0])

                    new_list = []

                    for v in user_list:
                        if v not in new_list:
                            new_list.append(v)

                    use_list = []
                    c=0
                    for user in users:
                        try:
                            refresh_token1 = user[1]
                            user_id = user[0]
                            if not user_id in use_list:
                                use_list.append(user_id)
                                if c>=until:
                                    com=True
                                    break
                                new_token = await refresh_token(refresh_token1)
                                if (new_token != False):
                                    new_refresh = new_token["refresh_token"]
                                    new_token = new_token["access_token"]
                                    ss = await add_user(new_token, message.guild.id, user_id)
                                    if ss == True:
                                        c += 1
                                    con, cur = start_db()
                                    cur.execute("UPDATE users SET token = ? WHERE token == ?;",
                                                (new_refresh, refresh_token1))
                                    con.commit()
                                    con.close()

                                else:
                                    con, cur = start_db()
                                    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
                                    con.commit()
                                    con.close()
                        except:
                            pass
            await message.author.send(embed=embed("success", '성공', "유저 복구가 완료되었습니다."))


client.run(settings.token)
