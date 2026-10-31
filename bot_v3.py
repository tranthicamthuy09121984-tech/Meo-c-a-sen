
# -*- coding: utf-8 -*-
import os
import asyncio
import base64
import io
import logging
from threading import Thread

import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask

from google import genai
import anthropic
from openai import OpenAI


# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MeoBot")


# ---------- Keep alive ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot của Sen đang thức! Hi Sennn"


def run():
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 10000))
    )


def keep_alive():
    Thread(target=run, daemon=True).start()


# ---------- API Keys ----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


# ---------- Client AI ----------
gemini_client = (
    genai.Client(api_key=GEMINI_API_KEY)
    if GEMINI_API_KEY else None
)

claude_client = (
    anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    if CLAUDE_API_KEY else None
)

openai_client = (
    OpenAI(api_key=OPENAI_API_KEY)
    if OPENAI_API_KEY else None
)

deepseek_client = (
    OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
    if DEEPSEEK_API_KEY else None
)


# ---------- Model IDs ----------
MODELS = {
    "claude": "claude-sonnet-5-5",
    "gemini": "gemini-3.6-flash",
    "chatgpt": "gpt-4o-mini",
    "deepseek": "deepseek-chat",
}

# User ID -> AI provider
chon_mo_hinh = {}


# ---------- Discord Bot ----------
intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"Đã đăng nhập: {bot.user}")

    if not getattr(bot, "synced", False):
        await bot.tree.sync()
        bot.synced = True
        print("Đã đồng bộ Slash Commands!")


# ---------- GPT IMAGE 2 ----------
def tao_anh(prompt: str) -> bytes:
    if openai_client is None:
        raise RuntimeError("Chưa cấu hình OPENAI_API_KEY!")

    response = openai_client.images.generate(
        model="gpt-image-2",
        prompt=prompt
    )

    if not response.data or not response.data[0].b64_json:
        raise RuntimeError("API không trả về dữ liệu hình ảnh.")

    return base64.b64decode(response.data[0].b64_json)


@bot.tree.command(
    name="image",
    description="Tạo ảnh bằng GPT Image 2"
)
@app_commands.describe(
    prompt="Mô tả hình ảnh bạn muốn tạo"
)
async def image(
    interaction: discord.Interaction,
    prompt: str
):
    prompt = prompt.strip()

    if not prompt:
        await interaction.response.send_message(
            "Bạn chưa nhập mô tả hình ảnh!",
            ephemeral=True
        )
        return

    if openai_client is None:
        await interaction.response.send_message(
            "Bot chưa được cấu hình OPENAI_API_KEY!",
            ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True)

    try:
        image_bytes = await asyncio.to_thread(
            tao_anh,
            prompt
        )

        image_file = discord.File(
            io.BytesIO(image_bytes),
            filename="gpt_image_2.png"
        )

        embed = discord.Embed(
            title="✨ GPT Image 2",
            description="Hình ảnh đã được tạo thành công!",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="📝 Prompt",
            value=prompt[:1024],
            inline=False
        )

        embed.set_image(
            url="attachment://gpt_image_2.png"
        )

        embed.set_footer(
            text="Meo AI Image Generator"
        )

        await interaction.followup.send(
            embed=embed,
            file=image_file
        )

    except Exception as e:
        logger.exception("Image generation failed")

        await interaction.followup.send(
            f"❌ Không thể tạo ảnh.\nLỗi: `{str(e)[:800]}`"
        )


# ---------- Hey Meo ----------
@bot.tree.command(
    name="heymeo",
    description="Đánh thức Meo"
)
async def heymeo(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Hazz, hello {interaction.user.mention}"
    )


# ---------- Chọn mô hình ----------
@bot.tree.command(
    name="mo_hinh",
    description="Đổi mô hình ngôn ngữ"
)
@app_commands.describe(
    ten="Mô hình bạn muốn dùng"
)
@app_commands.choices(ten=[
    app_commands.Choice(name="Claude", value="claude"),
    app_commands.Choice(name="Gemini", value="gemini"),
    app_commands.Choice(name="ChatGPT", value="chatgpt"),
    app_commands.Choice(name="DeepSeek", value="deepseek"),
])
async def mo_hinh(
    interaction: discord.Interaction,
    ten: app_commands.Choice[str]
):
    chon_mo_hinh[interaction.user.id] = ten.value

    await interaction.response.send_message(
        f"Đã đổi mô hình thành **{ten.name}**!"
    )


# ---------- Hàm gọi AI ----------
def hoi_ai(nha_cung_cap: str, message: str) -> str:
    model = MODELS[nha_cung_cap]

    if nha_cung_cap == "gemini":
        if gemini_client is None:
            raise RuntimeError("Chưa cấu hình GEMINI_API_KEY!")

        res = gemini_client.models.generate_content(
            model=model,
            contents=message
        )
        return res.text or "AI không trả về nội dung."

    if nha_cung_cap == "claude":
        if claude_client is None:
            raise RuntimeError("Chưa cấu hình CLAUDE_API_KEY!")

        res = claude_client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": message}
            ],
        )
        return res.content[0].text

    if nha_cung_cap == "chatgpt":
        if openai_client is None:
            raise RuntimeError("Chưa cấu hình OPENAI_API_KEY!")

        res = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": message}
            ],
        )
        return res.choices[0].message.content or "AI không trả lời."

    if nha_cung_cap == "deepseek":
        if deepseek_client is None:
            raise RuntimeError("Chưa cấu hình DEEPSEEK_API_KEY!")

        res = deepseek_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": message}
            ],
        )
        return res.choices[0].message.content or "AI không trả lời."

    raise ValueError(
        f"Không tìm thấy mô hình {nha_cung_cap}"
    )


# ---------- Chat ----------
@bot.tree.command(
    name="chat",
    description="Chat với Meo"
)
async def chat(
    interaction: discord.Interaction,
    message: str
):
    await interaction.response.defer()

    nha_cung_cap = chon_mo_hinh.get(
        interaction.user.id,
        "gemini"
    )

    try:
        tra_loi = await asyncio.to_thread(
            hoi_ai,
            nha_cung_cap,
            message
        )

        # Discord giới hạn nội dung mỗi tin nhắn 2000 ký tự
        for i in range(0, len(tra_loi), 2000):
            doan = tra_loi[i:i + 2000]

            if i == 0:
                await interaction.followup.send(doan)
            else:
                await interaction.channel.send(doan)

    except Exception as e:
        logger.exception("Chat failed")

        await interaction.followup.send(
            f"❌ Lỗi: `{str(e)[:800]}`"
        )


# ---------- Start Bot ----------
if not DISCORD_TOKEN:
    raise RuntimeError("Thiếu DISCORD_TOKEN!")

keep_alive()
bot.run(DISCORD_TOKEN)
