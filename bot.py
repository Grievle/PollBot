import discord
from discord.ext import commands
from discord.ext.commands import Bot
from dotenv import load_dotenv
import os
import asyncio

load_dotenv() 

intents = discord.Intents.all()
intents.typing = False
intents.presences = False
intents.messages = True

# import discord
# from discord.ext import commands

# intents = discord.Intents.default()
# intents.typing = False
# intents.presences = False
# intents.messages = True

# class MyBot(commands.Bot):
#     def __init__(self, command_prefix, intents):
#         super().__init__(command_prefix, intents=intents)

#     async def on_ready(self):
#         print(f'Logged in as {self.user.name} ({self.user.id})')
#         print('------')

#     @commands.command()
#     async def hello(self, ctx):
#         await ctx.send("안녕하세요!")

# bot = MyBot(command_prefix='!', intents=intents)
# bot.run('YOUR_BOT_TOKEN')

# import discord
# from discord.ext import commands

# intents = discord.Intents.default()
# intents.typing = False
# intents.presences = False

# bot = commands.Bot(command_prefix='!', intents=intents)

# @bot.event
# async def on_ready():
#     print(f'Logged in as {bot.user.name} ({bot.user.id})')
#     print('------')

# @bot.command()
# async def vote(ctx, question, *options):
#     if len(options) < 2:
#         await ctx.send("투표 옵션은 최소 2개 이상이어야 합니다.")
#         return

#     formatted_options = [f"{i+1}. {option}" for i, option in enumerate(options)]
#     formatted_question = f"**{question}**\n\n" + "\n".join(formatted_options)

#     embed = discord.Embed(title="투표", description=formatted_question, color=0x00ff00)
#     message = await ctx.send(embed=embed)

#     for i in range(len(options)):
#         await message.add_reaction(chr(127462 + i))

# bot.run('YOUR_BOT_TOKEN')

class PollBot(commands.Bot):

    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix, intents=intents)
        self.restart = False
        
        self.is_start = False
        self.candidate = -1
        self.timeout = 0
        self.cand2idx = [-1]
        self.thread_id = None
        self.voter = {}
        self.wait_task = None

    def value_init(self):
        self.is_start = False
        self.candidate = -1
        self.timeout = 0
        self.cand2idx = [-1]
        self.thread_id = None
        self.voter = {}
        self.wait_task = None

    # async def wait_duration(self, duration):
    #     print(f"Poll wait start {duration}")
    #     await asyncio.sleep(duration)
    #     print(f"Poll Over")


bot = PollBot(command_prefix='!', intents=intents) 

@bot.event
async def on_ready():
    print(f'logged in as {bot.user}')

@bot.command()
async def how(ctx):
    await ctx.send("해당 봇은 **투표**(`!vote`)와 **베팅**(`!betting`) 두가지 버전을 지원합니다.\n\n**투표 시작 방법**\n```!vote <duration> {<arg0> <arg1> ...}```\nex) **10**초동안 **[1]'술', [2]'사랑', [3]'기타'**로 투표를 진행한다. \n```!vote 10 술 사랑 기타```\n**베팅 시작 방법**\n```!betting <duration> <rank> {<arg0> <arg1> ...}```\nex) **10**초동안 **[1]'술', [2]'사랑', [3] '기타'**로 **2등** 베팅을 진행한다. \n```!betting 10 2 술 사랑 기타```\n\n**선택 방법**\n선택은 쓰레드에서 진행합니다.\n```!select 후보번호```\nex) **[3] '기타'**를 선택한다.\n```!select 3```")
    
@bot.command()
async def vote(ctx, timeout, *args):
    
    # block the other vote
    if bot.is_start:
        await ctx.reply('the other vote is processing!')
        return
    if not timeout.isnumeric():
        await ctx.reply('second argument must be a numeric')
        return
    duration = int(timeout)
    if duration < 10:
        await ctx.reply('please setting over than 10 second')
        return
    if duration > 60:
        await ctx.reply('please setting less than 60 second')
        return

    # Start poll
    bot.is_start = True
    print('Poll Start!')
    
    embed = discord.Embed(title="투표", description='dddd', color=discord.Color.blue())
    bot.candidate = 0
    for idx, cand in enumerate(args):
        embed.add_field(name=f"[{idx+1}]번 후보", value=cand, inline=False)
        bot.cand2idx.append(cand)
        bot.candidate += 1
    

    message = await ctx.send(embed=embed)
    new_thread = await message.channel.create_thread(name="투표 공간", message=message)
    bot.thread_id = new_thread.id
    await ctx.reply('해당 투표의 **쓰레드**를 확인해주세요!')
    await new_thread.send(f"@here\n쓰레드에서 투표를 진행합니다.\n투표는 **{duration}초**간 진행됩니다.\n```!select <num>```\n\nex) **[0]번 후보**를 투표한다면\n```!select 0```")
    
    # bot.wait_task = asyncio.create_task(bot.wait_duration(duration))
    
    await asyncio.sleep(duration)
    ## init 
    ## vote over
    bot.is_start = False
    await ctx.reply('**vote over!**')
    print("Vote Over!")
    result = [0] * (bot.candidate+1)
    for v in bot.voter:
        print(bot.voter, v, bot.voter[v], result)
        result[bot.voter[v][0]] += 1

    ## aggregate the reuslt of vote
    re = sorted([(r, idx) for idx, r in enumerate(result) if idx > 0], reverse=True)
    vote_result = ""
    last_print = ""
    for idx, r in enumerate(re):
        vote_result += f"\n[{r[1]}]\t{bot.cand2idx[r[1]]}\t{r[0]}표"
        if idx == 0:
            last_print += f":first_place: **{bot.cand2idx[r[1]]}**\t"
        elif idx == 1:
            last_print += f":second_place: **{bot.cand2idx[r[1]]}**\t"
        elif idx == 2:
            last_print += f":third_place: **{bot.cand2idx[r[1]]}**\t"
    bot.value_init()
    await ctx.reply('@here\n**vote result**```' + vote_result + f"```\n{last_print}")
    print("print the result!")

@bot.command()
async def betting(ctx, timeout, rank, *args):
    
    # block the other vote
    if bot.is_start:
        await ctx.reply('the other vote is processing!')
        return
    if not timeout.isnumeric():
        await ctx.reply('second argument must be a numeric')
        return
    if not rank.isnumeric():
        await ctx.reply('third argument must be a numeric')
        return
    duration = int(timeout)
    if duration < 10:
        await ctx.reply('please setting over than 10 second')
        return
    if duration > 60:
        await ctx.reply('please setting less than 60 second')
        return

    # Start poll
    bot.is_start = True
    print('Poll Start!')
    
    embed = discord.Embed(title="베팅", description=f'{rank}등 할 것 같은 사람을 골라주세요.', color=discord.Color.blue())
    bot.candidate = 0
    for idx, cand in enumerate(args):
        embed.add_field(name=f"[{idx+1}]번 후보", value=cand, inline=False)
        bot.cand2idx.append(cand)
        bot.candidate += 1
    

    message = await ctx.send(embed=embed)
    new_thread = await message.channel.create_thread(name="베팅 공간", message=message)
    bot.thread_id = new_thread.id
    await ctx.reply('해당 베팅의 **쓰레드**를 확인해주세요!')
    await new_thread.send(f"@here\n쓰레드에서 베팅을 진행합니다.\n베팅는 **{duration}초**간 진행됩니다.\n```!select <num>```\n\nex) **[0]번 후보**를 베팅한다면\n```!select 0```")
    
    # bot.wait_task = asyncio.create_task(bot.wait_duration(duration))
    
    await asyncio.sleep(duration)
    ## init 
    ## vote over
    bot.is_start = False
    await ctx.reply('**bet over!**')
    print("Bet Over!")
    result = [[] for _ in range(bot.candidate+1)]
    for v in bot.voter:
        print(bot.voter, v, bot.voter[v], result)
        result[bot.voter[v][0]].append(bot.voter[v][1])

    ## aggregate the reuslt of vote

    vote_result = ""
    last_print = ""
    print(bot.cand2idx)
    for idx, r in enumerate(result[1:]):
        vote_result += f"\n```[{idx+1}]\t{bot.cand2idx[idx+1]}\t{len(r)}표```-> "
        for vv in r:
            vote_result += f"{vv} / "
    bot.value_init()
    await ctx.reply('@here\n**betting result**' + vote_result + f"\n{last_print}")
    print("print the result!")

# @bot.command()
# async def stop(ctx):
#     if bot.is_start:
#         bot.task.cancel()
#         try:
#             await bot.task
#         except asyncio.CancelledError:
#             print("Vote Cancelled")
#     else:
#         await ctx.reply('There is no vote processing')

@bot.command()
async def select(ctx, num):
    if isinstance(ctx.channel, discord.Thread):
        if ctx.message.channel.id != bot.thread_id:
            await ctx.message.reply('This thread is not for voting anymore.')
            return
        if not bot.is_start:
            await ctx.message.reply('There is no voting system')
            return
        if not num.isnumeric():
            await ctx.message.reply('please input the number')
            return
        print(int(num), bot.candidate+1)
        if int(num) < 1 or int(num) > bot.candidate:
            await ctx.message.reply('invalid candidate')
            return
        bot.voter[ctx.author.id] = (int(num),f"{ctx.message.author.display_name}")
        print(bot.voter, bot.candidate)
    
bot.run(os.getenv('TOKEN'))
    
