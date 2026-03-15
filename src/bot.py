import discord
from discord.ext import commands, tasks
import psutil
import subprocess
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
ALERT_CHANNEL_ID = int(os.getenv('ALERT_CHANNEL_ID'))
ALLOWED_USER_ID = int(os.getenv('ALLOWED_USER_ID'))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIRECTORY = os.path.join(BASE_DIR, "..", "scripts")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if not resource_monitor.is_running():
        resource_monitor.start()

@tasks.loop(seconds=60)
async def resource_monitor():
    def read_stat():
        with open('/host/proc/stat') as f:
            vals = list(map(int, f.readline().split()[1:8]))
        return vals[3] + vals[4], sum(vals)

    idle1, total1 = read_stat()
    await asyncio.sleep(1)
    idle2, total2 = read_stat()
    diff_total = total2 - total1
    diff_idle = idle2 - idle1
    cpu_usage = round(100 * (diff_total - diff_idle) / diff_total, 1) if diff_total else 0.0

    mem = {}
    with open('/host/proc/meminfo') as f:
        for line in f:
            parts = line.split()
            mem[parts[0].rstrip(':')] = int(parts[1])
    ram_usage = round(100 * (mem['MemTotal'] - mem['MemAvailable']) / mem['MemTotal'], 1)

    if cpu_usage > 90.0 or ram_usage > 85.0:
        channel = bot.get_channel(ALERT_CHANNEL_ID)
        if channel:
            await channel.send(f"⚠️ **Server Resource Alert!**\n**CPU:** {cpu_usage}%\n**RAM:** {ram_usage}%")

# --- COMMAND GROUP ---

@bot.group(name="poseidon", invoke_without_command=True)
async def poseidon(ctx):
    """The main command. Shows help if no subcommand is used."""
    embed = discord.Embed(
        title="🔱 Poseidon Bot Control Panel",
        description="Available commands for server management:",
        color=discord.Color.gold()
    )
    embed.add_field(name="📊 `!poseidon stats`Standard text", value="View real-time CPU/RAM/Disk usage.", inline=False)
    embed.add_field(name="📂 `!poseidon scripts`Standard text", value="List all executable scripts in the scripts folder.", inline=False)
    embed.add_field(name="🚀 `!poseidon run <name>`Standard text", value="Execute a specific script (e.g., `!poseidon run hello`).", inline=False)
    embed.set_footer(text="Authorized users only.")
    await ctx.send(embed=embed)

@poseidon.command()
async def stats(ctx):
    """Fetch live server metrics."""

    def read_stat():
        with open('/host/proc/stat') as f:
            vals = list(map(int, f.readline().split()[1:8]))
        return vals[3] + vals[4], sum(vals)

    def get_host_ram():
        mem = {}
        with open('/host/proc/meminfo') as f:
            for line in f:
                parts = line.split()
                mem[parts[0].rstrip(':')] = int(parts[1])
        return round(100 * (mem['MemTotal'] - mem['MemAvailable']) / mem['MemTotal'], 1)

    def get_host_disk():
        st = os.statvfs('/host')
        total = st.f_blocks * st.f_frsize
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        return round(100 * used / total, 1) if total else 0.0

    idle1, total1 = read_stat()
    await asyncio.sleep(1)
    idle2, total2 = read_stat()
    diff_total = total2 - total1
    diff_idle = idle2 - idle1
    cpu = round(100 * (diff_total - diff_idle) / diff_total, 1) if diff_total else 0.0

    ram = get_host_ram()
    disk = get_host_disk()

    embed = discord.Embed(title="📊 System Performance", color=discord.Color.blue())
    embed.add_field(name="CPU", value=f"```{cpu}%```", inline=True)
    embed.add_field(name="RAM", value=f"```{ram}%```", inline=True)
    embed.add_field(name="Disk", value=f"```{disk}%```", inline=True)
    await ctx.send(embed=embed)

@poseidon.command()
async def scripts(ctx):
    """List scripts in /scripts folder."""
    try:
        files = [f for f in os.listdir(SCRIPT_DIRECTORY) if f.endswith('.py')]
        msg = "\n".join([f"• `{f}`" for f in files]) if files else "No scripts found."
        await ctx.send(f"📂 **Available Scripts:**\n{msg}")
    except Exception as e:
        await ctx.send(f"❌ Error accessing directory: {e}")

@poseidon.command()
async def run(ctx, script_name: str):
    """Execute a script."""
    if ctx.author.id != ALLOWED_USER_ID:
        return await ctx.send("⛔ **Access Denied.**")

    if not script_name.endswith('.py'): script_name += '.py'
    script_path = os.path.join(SCRIPT_DIRECTORY, script_name)

    if not os.path.exists(script_path):
        return await ctx.send(f"❓ Script `{script_name}` not found.")

    await ctx.send(f"⚙️ Executing `{script_name}`...")

    try:
        result = subprocess.run(['python3', script_path], capture_output=True, text=True, timeout=30)
        output = result.stdout if result.returncode == 0 else result.stderr
        await ctx.send(f"✅ **Output:**\n```text\n{output[:1900] or 'Success (No Output)'}```")
    except Exception as e:
        await ctx.send(f"❌ **Execution Error:**\n`{e}`")

bot.run(TOKEN)