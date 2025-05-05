import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import hashlib
import datetime
import os
import random
import json
from dotenv import load_dotenv
import pickle

from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

# ✅ Load biến môi trường từ file .env
load_dotenv()
client = OpenAI()

EMAIL = "vietle11224@gmail.com"
PASSWORD = "THT@2024"
LOGIN_URL = "https://salework.net/login/"
CHAT_URL = "https://chat.salework.net/conversations"

DEFAULT_REPLY = "Cảm ơn bạn đã nhắn tin cho shop! Mình sẽ hỗ trợ bạn ngay nhé 💙"
CUSTOM_GPT_PROMPT = """
Bạn là nhân viên CSKH Shopee. Hãy trả lời khách bằng tiếng Việt thân thiện, đúng quy trình nếu có.
"""

# ✅ Tạo hoặc load FAISS
FAISS_INDEX_PATH = "doihang_index"
embeddings = OpenAIEmbeddings()

if os.path.exists(f"{FAISS_INDEX_PATH}/index.faiss"):
    faiss_index = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
else:
    with open("quytrinhdoihang.txt", "r", encoding="utf-8") as f:
        content = f.read()
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    docs = [Document(page_content=chunk) for chunk in splitter.split_text(content)]
    faiss_index = FAISS.from_documents(docs, embeddings)
    faiss_index.save_local(FAISS_INDEX_PATH)

# ✅ Ghi log
def log_message(customer, message, reply):
    with open("log.csv", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()}, {customer}, {message}, {reply}\n")

# ✅ Gọi GPT + context
def get_context(message):
    docs = faiss_index.similarity_search(message, k=1)
    return docs[0].page_content if docs else ""

def get_gpt_reply_with_context(message, context):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": CUSTOM_GPT_PROMPT},
                {"role": "user", "content": f"Khách: {message}\nQuy trình tham khảo: {context}"}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("GPT lỗi:", e)
        return DEFAULT_REPLY

# ✅ Phản hồi
async def get_reply(message):
    context = get_context(message)
    reply = get_gpt_reply_with_context(message, context)
    if not reply or len(reply.strip()) < 5:
        return DEFAULT_REPLY
    return reply

# ✅ Đăng nhập Salework
async def login_salework(page):
    await page.goto(LOGIN_URL)
    await page.fill('input[type="text"]', EMAIL)
    await page.fill('input[type="password"]', PASSWORD)
    await page.click('button[type="submit"]')
    await page.wait_for_timeout(5000)
    print("✅ Đăng nhập thành công")

# ✅ Bot chính
async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await login_salework(page)
        await page.goto(CHAT_URL)
        await page.wait_for_selector("div.conversation-list-content", timeout=60000)

        while True:
            convo_elements = await page.query_selector_all("div.conversation-list-content > div > div")

            for i in range(len(convo_elements)):
                try:
                    # Load lại danh sách hội thoại mỗi vòng để đảm bảo valid handle
                    convo_elements = await page.query_selector_all("div.conversation-list-content > div > div")
                    convo = convo_elements[i]

                    await convo.scroll_into_view_if_needed()
                    await convo.click()
                    await asyncio.sleep(2)
                    await page.wait_for_selector("div.chat-box-content", timeout=10000)

                    customer = await page.inner_text(".chat-box .d-flex.align-items-center span")
                    messages = await page.query_selector_all(
                        "div.chat-box-content div.blockChat-left, div.chat-box-content div.blockChat-right")
                    if not messages:
                        continue

                    last_msg = messages[-1]
                    last_msg_class = await last_msg.get_attribute("class")
                    if "blockChat-left" not in last_msg_class:
                        continue

                    msg_text = await last_msg.inner_text()
                    reply = await get_reply(msg_text)
                    print(f"💬 {msg_text}\n↪️ {reply}")
                    await page.fill("#textarea", reply)
                    await page.keyboard.press("Enter")
                    log_message(customer, msg_text, reply)

                except Exception as e:
                    print("❌ Lỗi hội thoại:", e)
                    continue

            print("⏳ Chờ 5 phút rồi quét lại...\n")
            await asyncio.sleep(300)

asyncio.run(run())
