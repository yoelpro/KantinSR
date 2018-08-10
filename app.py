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
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage,
    BubbleContainer, ImageComponent, BoxComponent, TextComponent,
    SpacerComponent, IconComponent, ButtonComponent, SeparatorComponent,
    URIAction, ButtonsTemplate, PostbackAction, MessageAction,
    TemplateSendMessage, rich_menu, imagemap, ImageCarouselTemplate,
    ImageCarouselColumn, CarouselTemplate, CarouselColumn, PostbackEvent,
    FollowEvent
)

# site url
base_url = os.getenv('BASE_URL', None)

statics_url = base_url + '/static'

# database url
DATABASE_URL = os.getenv('DATABASE_URL', None)

# bot prefix
BOT_PREFIX = os.getenv('BOT_PREFIX', '!')

# menu list
RICE_TYPE = [x.strip() for x in os.getenv('RICE_TYPE', '').split(';')]
TOPPING_TYPE = [x.strip() for x in os.getenv('TOPPING_TYPE', '').split(';')]
SAUCE_TYPE = [x.strip() for x in os.getenv('SAUCE_TYPE', '').split(';')]
app = Flask(__name__)

# admin uid
ADMIN = os.getenv('ADMIN', None)
# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

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
    # check bot prefix
    if event.message.text.startswith(BOT_PREFIX):
        # seperate message contents as command and arguments
        message_body = event.message.text.strip()[1:].split()
        command = message_body[0]
        if(len(message_body) >= 2): #kalau ada 2 kata atau lebih
            arguments_list = message_body[1:]
            arguments_string = ' '.join(arguments_list)
        else:
            arguments_list = []
            arguments_string = ''

        # set database connection
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        if command == 'pesan':
            order_memo = BOT_PREFIX + command + ' ' + arguments_string
            if len(arguments_list) == 0: #pilih nasi
                pilihan_menu = ImageCarouselTemplate(columns=[
                    ImageCarouselColumn(
                        image_url=statics_url + '/nasi_putih.jpg',
                        action=MessageAction(label='Nasi Putih', text=BOT_PREFIX + command + ' putih')
                        ),
                    ImageCarouselColumn(
                        image_url=statics_url + '/nasi_umami.jpg',
                        action=MessageAction(label='Nasi Umami', text=BOT_PREFIX + command + ' umami')
                        )
                ])
                menu_pesan = TemplateSendMessage(
                    alt_text='Menu pesanan', template=pilihan_menu)
                
                line_bot_api.reply_message(event.reply_token, menu_pesan)
            
            elif len(arguments_list) == 1: #pilih topping
                if RICE_TYPE.count(arguments_list[0]) == 1:
                    pilihan_menu = ImageCarouselTemplate(columns=[
                        ImageCarouselColumn(
                            image_url=statics_url + '/topping_ayam.jpg',
                            action=MessageAction(label='Ayam', text=order_memo + ' ayam')
                            ),
                        ImageCarouselColumn(
                            image_url=statics_url + '/topping_cumi.jpg',
                            action=MessageAction(label='Cumi', text=order_memo + ' cumi')
                            ),
                        ImageCarouselColumn(
                            image_url=statics_url + '/topping_campur.jpg',
                            action=MessageAction(label='Campur', text=order_memo + ' campur')
                            )
                    ])
                    menu_pesan = TemplateSendMessage(
                        alt_text='Menu pesanan', template=pilihan_menu)
                    
                    line_bot_api.reply_message(event.reply_token, menu_pesan)

                else:
                    order_mistake(event)

            elif 2 <= len(arguments_list) <= 5 and arguments_list[-1] != 'selesai': #sedang milih saus
                if validate_order(arguments_list, -1):
                    sauce_template = ImageCarouselTemplate(columns=[
                        ImageCarouselColumn(
                            image_url=statics_url + '/sauce_xo.jpg',
                            action=MessageAction(label='XO', text=order_memo + ' xo')
                            ),
                        ImageCarouselColumn(
                            image_url=statics_url + '/sauce_mayo.jpg',
                            action=MessageAction(label='Mayonnaise', text=order_memo + ' mayo')
                            ),
                        ImageCarouselColumn(
                            image_url=statics_url + '/sauce_bali.jpg',
                            action=MessageAction(label='Bumbu Bali', text=order_memo + ' bali')
                            ),
                        ImageCarouselColumn(
                            image_url=statics_url + '/sauce_blackpepper.jpg',
                            action=MessageAction(label='Blackpepper', text=order_memo + ' blackpepper')
                            )
                    ])
                    sauce_choice = TemplateSendMessage(
                        alt_text='Menu saus', template=sauce_template)
                    
                    confirm_button = ButtonsTemplate(
                        text=('Pesananmu sekarang:' +
                            '\nNasi       : ' + arguments_list[0] +
                            '\nTopping    : ' + arguments_list[1] +
                            '\nSaus(max 4): ' + ', '.join(arguments_list[2:])),
                        actions=[
                            MessageAction(label='Selesai memesan', text=order_memo + ' selesai')
                        ])
                    order_confirm = TemplateSendMessage(
                        alt_text='Pesanan saat ini', template=confirm_button)

                    line_bot_api.reply_message(event.reply_token, [sauce_choice, order_confirm])
                
                else:
                    order_mistake(event)

            elif (len(arguments_list) == 6) and (arguments_list[-1] != 'selesai'): #selesai memesan semua saus
                if validate_order(arguments_list, -1):
                    summary_button = ButtonsTemplate(
                        text=('Apakah pesanan sudah benar?' +
                            '\nNasi       : ' + arguments_list[0] +
                            '\nTopping    : ' + arguments_list[1] +
                            '\nSaus(max 4): ' + ', '.join(arguments_list[2:])),
                        actions=[
                            MessageAction(label='Selesai memesan', text=order_memo + ' selesai')
                        ])
                    order_summary = TemplateSendMessage(
                        alt_text='Konfirmasi pesanan', template=summary_button)

                    line_bot_api.reply_message(event.reply_token, order_summary)

            elif len(arguments_list) >= 3 and arguments_list[-1] == 'selesai': #selesai memesan tpi tidak perlu semua saus
                if validate_order(arguments_list, -2):
                    db.tambahPesanan(
                        db.countRow('QUEUE', conn.cursor()) + 1,
                        event.source.user_id,
                        arguments_list[0],
                        arguments_list[1],
                        ', '.join(arguments_list[2:]),
                        cur
                        )
                    conn.commit()
                    reply(event, 'Pesanan sudah dikirim!')

                else:
                    order_mistake(event)

            else:
                order_mistake(event)
        
        elif command == 'cek':
            if arguments_list[0] == 'saldo':
                if event.source.type == 'user':
                    saldo = db.checkSaldo(event.source.user_id, cur)
                    reply(event, 'Saldo anda sekarang: ' + str(saldo))

                else:
                    reply(event, 'Perintah hanya dapat dilakukan melalui personal chat.')
                
            elif arguments_list[0] == 'antrian':
                if event.source.type == 'user':
                    response = db.checkStatus(event.source.user_id, cur)
                    reply(event, response)

                else:
                    reply(event, 'Perintah hanya dapat dilakukan melalui personal chat.')

        elif command == 'ok':
                if ADMIN.count(event.source.user_id) == 1:
                    if event.source.type == 'user':
                        for x in arguments_list:
                            db.selesaiPesanan(int(x), cur)
                    else:
                        reply(event, 'Perintah hanya dapat dilakukan melalui personal chat.')
                texts = db.listOrders(cur)
                for text in texts:
                    pm(ADMIN, text)
        conn.commit()
    # input = event.message.text
    # if input == '/profile':
    #     profile = line_bot_api.get_profile(event.source.user_id)
    #     profileName = profile.display_name
    #     profileId = profile.user_id
    #     profileStatus = profile.status_message
    #     profileData = 'Nama: ' + profileName + '\n'
    #     profileData = profileData + 'Id: ' + profileId + '\n'
    #     profileData = profileData + 'Status: ' + profileStatus
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text=profileData))

    # elif input == '/send':
    #     pm('Ufda14dbdecc124e76f3b491104bbcb43','Ada yang mau pesen')

    # elif input == '/status':
    #     profile = line_bot_api.get_profile(event.source.user_id)
    #     profileId = profile.user_id
    #      #setup database connection
    #     print('Successfully connected')
    #     cur = cur #create cursor
    #     text = db.checkStatus(profileId,cur)
    #     pm(profileId, text) #push message text
    #     conn.close() #close connection
    #     print('Database connection closed.')

    # elif input == '/jlhpesan':
    #     profile = line_bot_api.get_profile(event.source.user_id)
    #     profileId = profile.user_id
    #     conn = db.connect()
    #     print('Successfully connected')
    #     cur = conn.cursor()
    #     texts = db.listOrders(cur)
    #     for text in texts:
    #         pm(profileId, text)
    #     conn.close()
    #     print('Database connection closed.')
        
@handler.add(FollowEvent)
def followReply(event):
    uId = event.source.user_id
    uIdText = "'" + uId + "'"
    # conn = db.connect()
    print('Successfully connected')
    # cur = conn.cursor()
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

def validate_order(arguments_list, last_index):
    if ((RICE_TYPE.count(arguments_list[0]) == 1) and
    (TOPPING_TYPE.count(arguments_list[1]) == 1) and
    ([SAUCE_TYPE.count(x) for x in arguments_list[2:last_index]].count(0) == 0)):
        return True
    else:
        return False

def order_mistake(event):
    reply(event, 'Format pesanan salah!')


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
