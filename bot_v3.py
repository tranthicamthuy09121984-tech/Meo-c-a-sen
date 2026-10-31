# -*- coding: utf-8 -*-
import os
import asyncio
from threading import Thread
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from google import genai
import anthropic
from openai import OpenAI
import base64
import io
import logging

# ---------- Keep alive ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot của Sen đang thức! Hi Sennn"

def run():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

def keep_alive():
    Thread(target=run, daemon=True).start()

# ---------- Client AI ----------
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
claude_client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY") or "chua-co-key")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or "chua-co-key")
deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY") or "chua-co-key",
    base_url="https://api.deepseek.com",
)

MODELS = {
    "claude":   "claude-sonnet-5-5",
    "gemini":   "gemini-3.6-flash",  # kiểm tra lại ID trên ai.google.dev/models
    "chatgpt":  "gpt-4o-mini",
    "deepseek": "deepseek-chat",
}

chon_mo_hinh = {}  # user_id -> nhà cung cấp

# ---------- Bot ----------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Đã đăng nhập: {bot.user}")

@bot.tree.command("name="image", description="Image với GPT Image 2")
def image(interaction: discord.Interaction str):
    stream = openai_client.responses.create(
        model=MODELS["chatgpt"],  # "gpt-6-luna"
        service_tier="fast",
        input=message,
        text={"format": {"type": "text"}, "verbosity": "high"},
        reasoning={"effort": "max", "mode": "pro", "summary": "auto"},
        tools=[],
        stream=True,
        store=True,
        include=["reasoning.encrypted_content", "web_search_call.action.sources"],
    )

    ket_qua = []
    for event in stream:
        if event.type in ("response.output_text.delta", "response.refusal.delta"):
            ket_qua.append(event.delta)
        elif event.type == "error":
            raise RuntimeError(event.message)
        elif event.type == "response.failed":
            raise RuntimeError(event.response.error)
    return "".join(ket_qua)

@bot.tree.command(name="heymeo", description="Đánh thức Meo")
async def heymeo(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Hazz, hello {interaction.user.mention}"
    )

@bot.tree.command(name="mo_hinh", description="Đổi mô hình ngôn ngữ")
@app_commands.describe(ten="Mô hình bạn muốn dùng")
@app_commands.choices(ten=[
    app_commands.Choice(name="Claude",   value="claude"),
    app_commands.Choice(name="Gemini",   value="gemini"),
    app_commands.Choice(name="ChatGPT",  value="chatgpt"),
    app_commands.Choice(name="DeepSeek", value="deepseek"),
])
async def mo_hinh(interaction: discord.Interaction, ten: app_commands.Choice[str]):
    chon_mo_hinh[interaction.user.id] = ten.value
    await interaction.response.send_message(f"Đã đổi mô hình {ten.name}!")

def hoi_ai(nha_cung_cap: str, message: str) -> str:
    model = MODELS[nha_cung_cap]

    if nha_cung_cap == "gemini":
        res = gemini_client.models.generate_content(model=model, contents=message)
        return res.text

    if nha_cung_cap == "claude":
        res = claude_client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": message}],
        )
        return res.content[0].text

    if nha_cung_cap == "chatgpt":
        res = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message}],
        )
        return res.choices[0].message.content

    if nha_cung_cap == "deepseek":
        res = deepseek_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message}],
        )
        return res.choices[0].message.content

    raise ValueError(f"Không tìm thấy mô hình {nha_cung_cap}")

@bot.tree.command(name="chat", description="Chat với Meo")
async def chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer()
    nha_cung_cap = chon_mo_hinh.get(interaction.user.id, "gemini")
    try:
        tra_loi = await asyncio.to_thread(hoi_ai, nha_cung_cap, message)
        await interaction.followup.send(tra_loi[:2000])
    except Exception as e:
        await interaction.followup.send(f"Lỗi: {e}")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))