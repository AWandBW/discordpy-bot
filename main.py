# This example requires the 'message_content' privileged intents
import discord
import random
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
YOUR_GUILD_ID = 1351657789075750942

# Check if the token is valid
if not TOKEN:
    print("❌ Bot token not found. Please set the DISCORD_BOT_TOKEN environment variable.")
    exit(1)

IMAGE_LIST = ["C:\\Users\\alexn\\Pictures\\fifa_cards\\bundesliga\\FC_Bayern_munich\\musiala_gold_91.png"]

user_collections = {}
user_coins = {}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    try:
        # Replace YOUR_GUILD_ID with the ID of your server
        guild = discord.Object(id=YOUR_GUILD_ID)
        await bot.tree.sync(guild=guild)
        print(f'✅ Successfully synced commands for guild {YOUR_GUILD_ID}.')
    except Exception as e:
        print(f'❌ Error syncing commands: {e}')

@bot.tree.command(name="pack", description="Open a pack!")
async def store(interaction: discord.Interaction):
    if not IMAGE_LIST:
        await interaction.response.send_message("❌ No images available to open a pack.", ephemeral=True)
        return

    pack_content = random.choice(IMAGE_LIST)
    if not os.path.exists(pack_content):
        await interaction.response.send_message("❌ The selected pack content is missing.", ephemeral=True)
        return

    filename = os.path.basename(pack_content)
    embed = discord.Embed(title="🎁 You opened a pack!", color=discord.Color.gold())
    embed.set_image(url=f"attachment://{filename}")

    file = discord.File(pack_content, filename=filename)
    view = CollectionView(interaction.user.id, pack_content)
    view.message = await interaction.response.send_message(embed=embed, file=file, view=view)

@bot.tree.command(name="ping", description="Test if the bot is working")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

class CollectionView(discord.ui.View):
    def __init__(self, user_id, random_card):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.card_name = os.path.basename(random_card)
        self.message = None

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)
        await self.message.channel.send("⏳ The interaction has timed out.")

    @discord.ui.button(label="Save to Collection", style=discord.ButtonStyle.success)
    async def save_card(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id not in user_collections:
            user_collections[self.user_id] = {}

        if self.card_name in user_collections[self.user_id]:
            user_collections[self.user_id][self.card_name] += 1
        else:
            user_collections[self.user_id][self.card_name] = 1

        await interaction.response.send_message(f"✅ Added **{self.card_name}** to your collection!", ephemeral=False)

    @discord.ui.button(label="Quick Sell (Earn 50 Coins)", style=discord.ButtonStyle.danger)
    async def quick_sell(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_coins[self.user_id] = user_coins.get(self.user_id, 0) + 50
        await interaction.followup.send("💰 You sold the card for **50 coins**!", ephemeral=True)

@bot.tree.command(name="collection", description="View your collected cards")
async def collection(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in user_coins:
        user_coins[user_id] = 0
    if user_id not in user_collections:
        user_collections[user_id] = {}
    collected_cards = user_collections.get(user_id, {})

    embed = discord.Embed(title=f"{interaction.user.name}'s Collection", color=discord.Color.blue())

    if collected_cards:
        files = []
        for card, copies in collected_cards.items():
            image_path = next((c for c in IMAGE_LIST if os.path.basename(c) == card), None)
            if image_path and os.path.exists(image_path):
                file = discord.File(image_path, filename=card)
                files.append(file)
                embed.add_field(name=card, value=f"Copies: {copies}", inline=False)
        
        if files:
            embed.set_image(url=f"attachment://{files[0].filename}")
            await interaction.response.send_message(embed=embed, files=files)
        else:
            embed.description = "No images found for your collected cards."
            await interaction.response.send_message(embed=embed)
    else:
        embed.description = "You haven't collected any cards yet! Start opening packs to collect cards."
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="coins", description="Check your coin balance")
async def coins(interaction: discord.Interaction):
    print("✅ /coins command registered")
    try:
        user_id = interaction.user.id
        if user_id not in user_coins:
            user_coins[user_id] = 0
        if user_id not in user_collections:
            user_collections[user_id] = {}
        balance = user_coins.get(user_id, 0)
        print(f"User {interaction.user.name} (ID: {user_id}) has {balance} coins.")
        await interaction.response.send_message(f"💰 You have **{balance}** coins.", ephemeral=False)
    except Exception as e:
        print(f"❌ Error in /coins command: {e}")
        if not interaction.response.is_done():
            await interaction.response.defer(thinking=True)
        await interaction.followup.send("❌ An error occurred while fetching your balance.", ephemeral=False)

bot.run(TOKEN)
