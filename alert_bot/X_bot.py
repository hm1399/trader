import requests
from requests_oauthlib import OAuth1

# 设置认证信息
consumer_key = 'S6Y9hKslNqNlD3iSyOr2TmZTu'
consumer_secret = 'Vej8mxTJxQlNh5K75Yx33nxnXPjdxW39ezahsCJB2jwrQSo308'
access_token = '1943147050289500161-qzPduVhvhASsRw4r0ysFscfjWxLhFw'
access_token_secret = 'WghvY5QVWsNqFg4tvcDDDHoKusnfFAFPGWKShcLy8lwzL'

# 创建 OAuth1 对象
auth = OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)

# 构建发送消息的 URL
url = "https://api.twitter.com/1.1/direct_messages/events/new.json"

# 消息内容
message_data = {
    "event": {
        "type": "message_create",
        "message_create": {
            "target": {
                "recipient_id": "1945789697579732992"  # 替换为目标用户的 user_id
            },
            "message_data": {
                "text": "Hello, this is a test message!"
            }
        }
    }
}

# 发送请求
response = requests.post(url, auth=auth, json=message_data)

# 检查响应
if response.status_code == 200:
    print("Message sent successfully!")
else:
    print(f"Error: {response.status_code} - {response.text}")