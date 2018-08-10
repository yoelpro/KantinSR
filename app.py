# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
import json
import requests
import datetime
import os
import sys
import psycopg2
import db
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    FollowEvent, MessageEvent, TextMessage, TextSendMessage, AudioMessage, ImageMessage,
)

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
admin = os.getenv('ADMIN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'
# @handler.add(PostbackEvent)
# def balasPesanan(event):

@handler.add(MessageEvent, message=TextMessage)
def replyText(event):
    input = event.message.text
    if input == '/profile':
        profile = line_bot_api.get_profile(event.source.user_id)
        profileName = profile.display_name
        profileId = profile.user_id
        profileStatus = profile.status_message
        profileData = 'Nama: ' + profileName + '\n'
        profileData = profileData + 'Id: ' + profileId + '\n'
        profileData = profileData + 'Status: ' + profileStatus
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=profileData))

    elif input == '/send':
        pm('Ufda14dbdecc124e76f3b491104bbcb43','Ada yang mau pesen')

    elif input == '/status':
        profile = line_bot_api.get_profile(event.source.user_id)
        profileId = profile.user_id
        conn = db.connect() #setup database connection
        print('Successfully connected')
        cur = conn.cursor() #create cursor
        text = db.checkStatus(profileId,cur)
        pm(profileId, text) #push message text
        conn.close() #close connection
        print('Database connection closed.')

    elif input == '/jlhpesan':
        profile = line_bot_api.get_profile(event.source.user_id)
        profileId = profile.user_id
        conn = db.connect()
        print('Successfully connected')
        cur = conn.cursor()
        texts = db.listOrders(cur)
        for text in texts:
            pm(profileId, text)
        conn.close()
        print('Database connection closed.')
    elif '/ok' in input:    
        query = input.split(' ')
        nomorPesanan = int(query[1])
        conn = db.connect()
        print('Successfully connected')
        cur = conn.cursor()
        db.selesaiPesanan(nomorPesanan,cur)
        #listing
        texts = db.listOrders(cur)
        for text in texts:
            pm(admin, text)
        conn.close()
    else:
        if '/ok' in input:
            print True
        else:
            print False
        reply(event,event.message.text)

@handler.add(FollowEvent)
def followReply(event):
    uId = event.source.user_id
    uIdText = "'"+uId+"'"
    conn = db.connect()
    print('Successfully connected')
    cur = conn.cursor()
    cur.execute("SELECT EXISTS (SELECT 1 FROM CUSTOMERS WHERE uid = " + uIdText +");")
    exists = cur.fetchone()[0]
    if exists:
        saldo = db.checkSaldo(uId,cur)
        pm(uId,'Akun anda sudah pernah dibuat! \nSisa saldo: Rp '+ str(saldo))
    else:
        pm(uId,'Akun anda telah dibuat secara otomatis. \nSaldo anda sekarang: Rp 0.0')
        row = db.countRow('CUSTOMERS',cur)
        db.insertDataCustomer(row+1,uId,0,cur)
    pm(uId,'Silahkan kunjungi stand nasjep jika ingin mengisi saldo')
    conn.commit()
    conn.close()


# shortening
def reply(event, isi): #reply message
    line_bot_api.reply_message(event.reply_token,TextSendMessage(text=isi))
def pm(target_id, isi): #push message
    line_bot_api.push_message(target_id,TextSendMessage(text=isi))

if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
