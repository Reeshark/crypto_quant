import itchat
import time
from itchat.content import TEXT

# hotReload=True
# itchat.auto_login()

# 定义自动登录函数
# def auto_login():
#     itchat.auto_login(hotReload=True)  # 使用hotReload=True可以在登录后刷新网页
#     return itchat.get_contact()

#
# # 定义发送消息函数
# def send_message(nickname, message):
#     # 获取联系人列表
#     contacts = auto_login()
#
#     # 搜索指定昵称的联系人
#     try:
#         userinfo = itchat.search_friends(nickname="KIRIBATI")
#         # 确保搜索结果不为空
#         if userinfo:
#             # 发送消息给找到的第一个联系人
#             itchat.send(message, toUserName=userinfo[0]['UserName'])
#             print(f"消息已发送给：{userinfo[0]['NickName']}")
#         else:
#             print(f"未找到昵称为 {nickname} 的用户")
#     except Exception as e:
#         print(f"发送消息时发生错误：{e}")


# 要发送的消息内容
message_content = "auto-sending"

# 要发送消息的好友昵称
friend_nickname = "KIRIBATI"

itchat.auto_login(hotReload=True)
users = itchat.search_friends(name=friend_nickname)
userName = users[0]['UserName']
cnt=0
while(1):
    itchat.send("testing:%d"%cnt,toUserName=userName)
    time.sleep(2)
    cnt+=1
#itchat.run()
# 发送消息
#send_message(friend_nickname, message_content)