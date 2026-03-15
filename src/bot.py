import discord
from discord.ext import commands, tasks
import psutil
import subprocess
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
ALERT_CHANNEL_ID = int(os.getenv('ALERT_CHANNEL_ID'))
ALLOWED_USER_ID = int(os.getenv('ALLOWED_USER_ID'))
SCRIPT_DIRECTORY = '/app/scripts/' # This maps to your host's ./scripts folder

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    resource_monitor.start()

@tasks.loop(seconds=60)
async def resource_monitor():
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent

    if cpu_usage > 90.0 or ram_usage > 85.0:
        channel = bot.get_channel(ALERT_CHANNEL_ID)
        if channel:
            await channel.send(f"⚠️ **Server Resource Alert!**\n**CPU:** {cpu_usage}%\n**RAM:** {ram_usage}%")

@bot.command()
async def runscript(ctx, script_name: str):
    if ctx.author.id != ALLOWED_USER_ID:
        await ctx.send("You do not have permission to execute server scripts.")
        return

    if not script_name.endswith('.py'):
        script_name += '.py'
        
    script_path = os.path.join(SCRIPT_DIRECTORY, script_name)

    if not os.path.exists(script_path):
        await ctx.send(f"Error: Script `{script_name}` not found in the scripts directory.")
        return

    await ctx.send(f"Executing `{script_name}`...")

    try:
        result = subprocess.run(['python', script_path], capture_output=True, text=True, timeout=30)
        output = result.stdout if result.returncode == 0 else result.stderr
        
        if not output:
            output = "Script executed successfully with no output."
            
        if len(output) > 1900:
            output = output[:1900] + "\n...[Output truncated]"
            
        await ctx.send(f"**Output:**\n```text\n{output}\n```")
        
    except subprocess.TimeoutExpired:
        await ctx.send("Error: Script execution timed out (exceeded 30 seconds).")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {str(e)}")

bot.run(TOKEN)