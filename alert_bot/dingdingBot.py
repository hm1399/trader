# !/usr/bin/env python

import argparse
import logging
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests

def setup_logger():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter('%(asctime)s %(name)-8s %(levelname)-8s %(message)s [%(filename)s:%(lineno)d]'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def send_custom_robot_group_message(access_token, secret, msg, at_user_ids=None, at_mobiles=None, is_at_all=False):
    """
    发送钉钉自定义机器人群消息
    :param access_token: https://oapi.dingtalk.com/robot/send?access_token=b4c3e18267cab65127807d9e75bb355e7e770fdb5853e0a7cf61882a0bae7157
    :param secret: 机器人安全设置的加签secret
    :param msg: 消息内容
    :param at_user_ids: @的用户ID列表
    :param at_mobiles: @的手机号列表
    :param is_at_all: 是否@所有人
    :return: 钉钉API响应
    """
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f'{timestamp}\n{secret}'
    hmac_code = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

    url = f'https://oapi.dingtalk.com/robot/send?access_token={access_token}&timestamp={timestamp}&sign={sign}'
    #对话框主体
    body = {
        "at": {
            "isAtAll": str(is_at_all).lower(),
            "atUserIds": at_user_ids or [],
            "atMobiles": at_mobiles or []
        },
        "text": {
            "content": msg
        },
        "msgtype": "text"
    }
    headers = {'Content-Type': 'application/json'}
    resp = requests.post(url, json=body, headers=headers)
    logging.info("钉钉自定义机器人群消息响应：%s", resp.text)
    return resp.json()


def main():
    at_all= False # 是否@所有人
    send_custom_robot_group_message(
        # token
        access_token="b4c3e18267cab65127807d9e75bb355e7e770fdb5853e0a7cf61882a0bae7157",
        # secret 如果bot的安全设置被设置成加签
        secret="SEC15ec58e644908b4145595732b7708f70a4e90b33857a75de1c8ac2320e35340b",
        #要发送的信息
        msg="Good Good Good",
        at_user_ids= None,
        at_mobiles= None,
        is_at_all=at_all
    )

if __name__ == '__main__':
    main()