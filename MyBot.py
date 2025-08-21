# imports all necessary functions for the AI to run
import os
import discord
import asyncio
from openai import OpenAI
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Debugging output, shows if both the Discord and OpenAI keys are loaded from the .env file
print("Loaded Discord token?", bool(TOKEN))
print("Loaded OpenAI key?", bool(OPENAI_API_KEY))

client = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Shows us if the bot has connected successfully inside the terminal
@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} global commands.")
    print(f"{bot.user} has connected to the server!")


@bot.event
async def on_message(msg: discord.Message):
    if msg.author.bot:
        return

    # If the bot is mentioned in server, gives basic info about itself
    if bot.user in msg.mentions:
        if isinstance(msg.channel, discord.TextChannel):
            await msg.channel.send(f"Hey I’m AquaBot, created by Jacob, {msg.author.mention}!")

    await bot.process_commands(msg)

# slash command, responds with a greeting
@bot.tree.command(name="hello", description="Says hello!")
async def hello(interaction: discord.Interaction):
    username = interaction.user.mention
    await interaction.response.send_message(f"Hello {username}!")

# main source code, allows for AI to use GPT4- mini to respond to user input
async def ai_complete(user_msg: str, system_msg: str | None = None) -> str:
    def _call():
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=(
                [{"role": "system", "content": system_msg},
                 {"role": "user", "content": user_msg}]
                if system_msg else user_msg
            ),
            max_output_tokens=400,
            temperature=0.7
        )
        return resp.output_text
    return await asyncio.to_thread(_call)

# slash command, ask user to input info which would be responded to by GPT-4o mini
@bot.tree.command(name="chat", description="Ask GPT-4o mini something")
@app_commands.describe(message="What do you want to say?")
async def chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=True)
    try:
        reply = await ai_complete(
            user_msg=message,
            system_msg="You are a helpful, concise Discord bot. Keep replies short unless asked."
        )
        if len(reply) > 1900:   # max character limit for discord messages
            reply = reply[:1900] + "…"
        await interaction.followup.send(reply)
    except Exception as e:
        await interaction.followup.send("Not enough credits.", ephemeral=True)  # credits needed for GPT to generate response
        print("AI error:", e)

# always used at end for the bot to run the .py program
bot.run(TOKEN)
