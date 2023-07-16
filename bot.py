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

class PollBot(commands.Bot):

    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix, intents=intents)

        self.is_start = False
        self.candidate = -1
        self.channel_id = None
        self.timeout = 0
        self.cand2idx = [-1]
        self.thread_id = None
        self.voter = {}
        self.wait_task = None
        self.mode = None
        self.user_id = None

    def value_init(self):
        self.is_start = False
        self.candidate = -1
        self.timeout = 0
        self.cand2idx = [-1]
        self.thread_id = None
        self.voter = {}
        self.wait_task = None
        self.mode = None
        self.channel_id = None
        self.user_id = None


bot = PollBot(command_prefix='!', intents=intents) 

@bot.event
async def on_ready():
    print(f'logged in as {bot.user}')

@bot.command()
async def how(ctx):
    await ctx.send("해당 봇은 **투표**(`!vote`)와 **베팅**(`!betting`) 두가지 버전을 지원합니다.\n\n**투표 시작 방법**\n```!vote {<arg0> <arg1> ...}```\nex) **[1]'술', [2]'사랑', [3]'기타'**로 투표를 진행한다. \n```!vote 술 사랑 기타```\n**베팅 시작 방법**\n```!betting <rank> {<arg0> <arg1> ...}```\nex) **[1]'술', [2]'사랑', [3] '기타'**로 **2등** 베팅을 진행한다. \n```!betting 2 술 사랑 기타```\n\n**선택 방법**\n선택은 쓰레드에서 진행합니다.\n```!select 후보번호```\nex) **[3] '기타'**를 선택한다.\n```!select 3```\n\n**투표 종료**\n```!stop```")
    
@bot.command()
async def vote(ctx, *args):
    
    # block the other vote
    if bot.is_start:
        await ctx.reply('the other vote is processing!')
        return

    # Start poll
    bot.is_start = True
    bot.mode = 'vote'
    print('[Request] Start Poll')
    print('---------- Poll Start! ----------')
    
    embed = discord.Embed(title="투표", description='인기투표', color=discord.Color.blue())
    bot.candidate = 0
    for idx, cand in enumerate(args):
        embed.add_field(name=f"[{idx+1}]번 후보", value=cand, inline=False)
        bot.cand2idx.append(cand)
        bot.candidate += 1
    print("[Candidate]")
    print(bot.cand2idx)

    message = await ctx.send(embed=embed)
    new_thread = await message.channel.create_thread(name="투표 공간", message=message)
    bot.thread_id = new_thread.id
    bot.channel_id = ctx.channel.id
    bot.user_id = ctx.author.id
    await ctx.reply(f'@here 해당 투표의 **쓰레드**인 {new_thread.mention}에서 투표를 진행해주세요!')
    await new_thread.send(f"쓰레드에서 투표를 진행합니다.\n```!select <num>```\n\nex) **[0]번 후보**를 투표한다면\n```!select 0```\n\n중복으로 하더라도 **마지막에 선택한 후보**만 유효합니다.")
    print("[Success] Create Poll")

@bot.command()
async def betting(ctx, rank, *args):
    
    # block the other vote
    if isinstance(ctx.channel, discord.Thread):
        await ctx.reply("poll can't create on Thread")
        return
    if bot.is_start:
        await ctx.reply('the other vote is processing!')
        return
    if not rank.isnumeric():
        await ctx.reply('second argument must be a numeric')
        return

    # Start poll
    bot.is_start = True
    bot.mode = 'betting'
    print('[Request] Start Poll')
    print('---------- Poll Start! ----------')
    
    embed = discord.Embed(title="베팅", description=f'[{rank}등] 할 것 같은 사람을 골라주세요.', color=discord.Color.blue())
    bot.candidate = 0
    for idx, cand in enumerate(args):
        embed.add_field(name=f"[{idx+1}]번 후보", value=cand, inline=False)
        bot.cand2idx.append(cand)
        bot.candidate += 1

    print("[Candidate]")
    print(bot.cand2idx)

    message = await ctx.send(embed=embed)
    new_thread = await message.channel.create_thread(name="베팅 공간", message=message)
    bot.thread_id = new_thread.id
    bot.channel_id = ctx.channel.id
    bot.user_id = ctx.author.id
    await ctx.reply(f'@here 해당 베팅의 **쓰레드**인 {new_thread.mention}에서 베팅을 진행해주세요!')
    await new_thread.send(f"쓰레드에서 베팅을 진행합니다.\n```!select <num>```\n\nex) **[0]번 후보**를 베팅한다면\n```!select 0```\n\n중복으로 하더라도 **마지막에 선택한 후보**만 유효합니다.")
    
    print("[Success] Create Poll")

@bot.command()
async def stop(ctx):
    # if ctx.author.id != bot.user_id:
    #     await ctx.reply('투표 생성자만 종료할 수 있습니다.')
    #     return
    if bot.is_start and ctx.channel.id == bot.channel_id:
        print('[Request] Stop Poll')
        print('[Selection]')
        print(bot.voter)
        if bot.mode == 'vote':
            ## vote over
            bot.is_start = False
            await ctx.reply('**vote over!**')
            
            result = [0] * (bot.candidate+1)
            for v in bot.voter:
                
                result[bot.voter[v][0]] += 1

            ## aggregate the reuslt of vote
            re = sorted([(r, idx) for idx, r in enumerate(result) if idx > 0], reverse=True)
            vote_result = "```"
            last_print = ""
            for idx, r in enumerate(re):
                vote_result += f"\n[{r[1]}]\t{bot.cand2idx[r[1]]}\t{r[0]}표"
                if idx == 0:
                    last_print += f":first_place: **{bot.cand2idx[r[1]]}**\t"
                elif idx == 1:
                    last_print += f":second_place: **{bot.cand2idx[r[1]]}**\t"
                elif idx == 2:
                    last_print += f":third_place: **{bot.cand2idx[r[1]]}**\t"
            vote_result += "```"
        elif bot.mode == 'betting':
            ## vote over
            bot.is_start = False
            await ctx.reply('**bet over!**')
            
            result = [[] for _ in range(bot.candidate+1)]
            for v in bot.voter:
                result[bot.voter[v][0]].append(bot.voter[v][1])

            ## aggregate the reuslt of vote

            vote_result = ""
            last_print = ""
            
            for idx, r in enumerate(result[1:]):
                vote_result += f"\n```[{idx+1}]\t{bot.cand2idx[idx+1]}\t{len(r)}표```선택한 사람: "
                for vv in r:
                    vote_result += f"@{vv} "
        
        await ctx.reply(f'@here\n**{bot.mode} result**' + vote_result + f"\n{last_print}")
        try:
            thread = await bot.fetch_channel(bot.thread_id)
            if isinstance(thread, discord.Thread):
                await thread.delete()
        except:
            pass
        bot.value_init()
        print("[Success] Print the result of poll")
        print("---------------------------------")
    else:
        await ctx.reply('There is no vote processing')

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
        if int(num) < 1 or int(num) > bot.candidate:
            await ctx.message.reply('invalid candidate')
            return
        bot.voter[ctx.author.id] = (int(num),f"{ctx.message.author.display_name}")
        await ctx.message.reply(f'**[투표완료]** [{int(num)}]번 후보 ({bot.cand2idx[int(num)]})')
        print(f'[LOG] {ctx.message.author.display_name}: {num}')
bot.run(os.getenv('TOKEN'))
    
