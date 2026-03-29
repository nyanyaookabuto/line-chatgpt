from flask import Flask, request
import os

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# Gemini 用
from openai import OpenAI

app = Flask(__name__)

# LINE環境変数
LINE_TOKEN = os.getenv("LINE_TOKEN")
LINE_SECRET = os.getenv("LINE_SECRET")

# Gemini環境変数
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 安全チェック
if not LINE_TOKEN:
    raise ValueError("LINE_TOKEN が設定されていません")
if not LINE_SECRET:
    raise ValueError("LINE_SECRET が設定されていません")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY が設定されていません")

configuration = Configuration(access_token=LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# Gemini クライアント
client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    handler.handle(body, signature)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text

    # Gemini APIで応答生成
    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": "あなたはユーザー専用の優しいAIです。"},
            {"role": "user", "content": user_text}
        ]
    )

    reply = response.choices[0].message.content

    # LINEに返信
    with ApiClient(configuration) as api_client:
        line_bot = MessagingApi(api_client)
        line_bot.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )

if __name__ == "__main__":
    # Render用ホスト指定
    app.run(host="0.0.0.0", port=10000)