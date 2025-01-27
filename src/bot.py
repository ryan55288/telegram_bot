from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton ,KeyboardButton,ReplyKeyboardMarkup
from telegram.ext import Filters, CallbackContext,CommandHandler,MessageHandler,ConversationHandler,CallbackQueryHandler,ChatMemberHandler
import json
from src import _button
from src import _config
from src import _sql
import logging
import datetime
import time
import os
from flask import Flask, request

app = Flask(__name__)

configPath = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))+"\config.ini"

os.makedirs("./log",exist_ok=True)
if not os.path.isfile(configPath):
    print("遗失config.ini....")
    token = input("please enter your token : ")
    f = open("config.ini","w+")
    f.close()
    import configparser
    config=configparser.ConfigParser()
    config['Telegram-BOT'] = {}
    config['Telegram-BOT']['token'] = token
    with open('config.ini', 'w') as a:
        config.write(a)
    a.close()

logging.basicConfig(level=logging.INFO,
            format='[%(asctime)s]  %(levelname)s [%(filename)s %(funcName)s] [ line:%(lineno)d ] %(message)s',
            datefmt='%Y-%m-%d %H:%M',
            handlers=[logging.StreamHandler(),logging.FileHandler(f'log//{time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())}.log', 'w', 'utf-8')])

keyboard = _button.Keyboard()
init = _config.BotConfig()

def runSQL():
    return _sql.DBHP("telegram-bot.db")
# 更新config table botuserName
runSQL().editBotusername(init.updater.bot.username)
# 封裝
def sendMenu(update:Update,context:CallbackContext):
    context.bot.send_message(chat_id = update.effective_chat.id,text=keyboard.adminUser,reply_markup = keyboard.adminUserMenu)
    inviteFriendsMenu(update,context)
    InvitationStatisticsSettlementBonusMenu(update,context)

def inviteFriendsMenu(update:Update,context:CallbackContext):
    sql=runSQL()
    inviteFriendsSet = "开启" if sql.inviteFriendsSet == "True" else "关闭"
    followChannelSet = "开启" if sql.followChannelSet == "True" else "关闭"
    followChannelSetText = f"目前状态(关注频道)：{followChannelSet}\n"
    inviteFriendsText = f"目前状态(邀请好友)：{inviteFriendsSet}\n{followChannelSetText}邀请指定人数：{sql.inviteFriendsQuantity}\n删除系统消息：{sql.deleteSeconds}秒\n重置天数：{sql.inviteFriendsAutoClearTime}"
    context.bot.send_message(chat_id = update.effective_chat.id,text=inviteFriendsText,reply_markup = keyboard.inviteFriendsMenu)

def InvitationStatisticsSettlementBonusMenu(update:Update,context:CallbackContext):
    sql=runSQL()
    invitationBonusSet = "开启" if sql.invitationBonusSet == "True" else "关闭"
    #jsonContactPerson = json.loads(sql.contactPerson)
    #contactPerson = "["+jsonContactPerson['contactPersonUsername']+"](tg://user?id="+jsonContactPerson['contactPersonId']+")"
    contactPerson = sql.contactPerson
    invitationBonusSetText = f"目前状态：{invitationBonusSet}\n邀请人数：{sql.inviteMembers}\n获得奖金：{sql.inviteEarnedOutstand}\n结算奖金：{sql.inviteSettlementBonus}\n联系人：{contactPerson}"
    context.bot.send_message(chat_id = update.effective_chat.id,text=invitationBonusSetText,reply_markup = keyboard.InvitationStatisticsSettlementBonusMenu,parse_mode="Markdown")

def startText(update:Update,context:CallbackContext):
    return context.bot.send_message(chat_id = update.effective_chat.id,text="What con this bot do?\nPlease tap on START",reply_markup=ReplyKeyboardMarkup(keyboard.wordFlowKeyboardButton))

# CommandHandler
def start(update:Update,context:CallbackContext):
    # 限制邀請人數才能發言
    if update.message.chat.type == 'private':
        startText(update,context)
        if str(update.effective_chat.id) == str(update.message.from_user.id):
            return WORKFLOW

def dealMessage(update:Update,context:CallbackContext):
    sql = runSQL()
    first_name = update.message.from_user.first_name
    mention = "[@"+first_name+"：](tg://user?id="+str(update.message.from_user.id)+")"

    def catchChannel():
        try:
            update.message.reply_to_message.forward_from_chat.type
            return True
        except AttributeError:
            return False
            
    def deleteMsgToSeconds(context: CallbackContext):
        context.bot.delete_message(chat_id=update.effective_chat.id,message_id=context.job.context)

    if sql.getIsManager(update.effective_user.id) == "False" or sql.getManager(update.effective_user.id) is None:
        if first_name != "Telegram":
            if catchChannel() == False:
                rightToSpeak = True
                inviteFriendsText=""
                followChannelText=""
                autoClearTimeText=""
                invitationBonusText=""
                inviteEarnedOutstandText=""
                if sql.inviteFriendsAutoClearTime != "0" and sql.getInviteFriendsSet() == "True":
                    autoClearTimeText = f"要在{sql.inviteFriendsAutoClearTime}天内"
                if sql.getInviteFriendsSet() == "True":
                        if sql.invitationBonusSet =="True":

                            fromUserId = str(update.message.from_user.id)
                            try:
                                #inviteEarnedOutstand = sql.bounsCount(fromUserId,update.message.chat.id)
                                inviteEarnedOutstand = sql.getOutstandingAmount(fromUserId,update.message.chat.id)
                                if inviteEarnedOutstand is None:
                                    inviteEarnedOutstand = 0
                                inviteEarnedOutstandText = f"，未结算{inviteEarnedOutstand}元"
                            except TypeError:
                                sql.insertInviteToMakeMoney(update.message.from_user.id,update.message.from_user.first_name,update.message.chat.id,update.message.chat.title,"{}","",update.message.from_user.username)
                                inviteEarnedOutstand = sql.bounsCount(fromUserId,update.message.chat.id)
                            inviteToMakeMoneyBeInvitedLen = sql.getInviteToMakeMoneyBeInvitedLen(update.message.from_user.id,update.message.chat.id)
                            if inviteToMakeMoneyBeInvitedLen == 0:
                                lenght = int(sql.inviteMembers)
                            elif inviteToMakeMoneyBeInvitedLen > int(sql.inviteMembers):
                                lenght = int(sql.inviteMembers) % inviteToMakeMoneyBeInvitedLen
                            elif inviteToMakeMoneyBeInvitedLen < int(sql.inviteMembers):
                                lenght = int(sql.inviteMembers)-inviteToMakeMoneyBeInvitedLen
                            elif inviteToMakeMoneyBeInvitedLen == int(sql.inviteMembers):
                                lenght = sql.inviteMembers
                            #jsonContactPerson = json.loads(sql.contactPerson)
                            #contactPerson = "["+jsonContactPerson['contactPersonUsername']+"](tg://user?id="+str(jsonContactPerson['contactPersonId'])+")"
                            contactPerson = sql.contactPerson
                            invitationBonusText = f"(邀请{lenght}人可赚{sql.inviteEarnedOutstand}元{inviteEarnedOutstandText}，满{sql.inviteSettlementBonus}元请联系 {contactPerson} )"

                        if sql.messageLimitToInviteFriends(update.message.from_user.id,update.message.chat.id) == False:
                            rightToSpeak = False
                            
                            len = int(sql.inviteFriendsQuantity) - int(sql.getDynamicInviteFriendsQuantity(update.message.from_user.id))
                            inviteFriendsText = f"{autoClearTimeText}邀请{str(len)}人进群"
                            if int(sql.getDynamicInviteFriendsQuantity(update.message.from_user.id)) > int(sql.inviteFriendsQuantity):
                                rightToSpeak = True
                                inviteFriendsText = ""
                try:
                    if context.bot.get_chat_member(int(sql.getChannelId()[0]),update.effective_user.id).status =="left":
                        if sql.getFollowChannelSet() == "True":
                            rightToSpeak = False
                            channelmark = "[@"+sql.channelLink[13:]+"]("+sql.channelLink+")"
                            if sql.getInviteFriendsSet() == "True":
                                followChannelText = f"并关注频道 {channelmark}"
                            elif sql.getInviteFriendsSet() == "False":
                                followChannelText = f"关注频道 {channelmark}"
                except Exception as e:
                    print("機器人尚未加入頻道"+str(e))
                if rightToSpeak == False:
                    context.bot.delete_message(chat_id=update.effective_chat.id,message_id=update.message.message_id)
                    messageId = context.bot.send_message(chat_id=update.effective_chat.id,text=f"{mention}{inviteFriendsText}{invitationBonusText}{followChannelText}后才能发言",parse_mode="Markdown",disable_web_page_preview=True).message_id
                    context.job_queue.run_once(deleteMsgToSeconds,int(sql.deleteSeconds), context=messageId)

# MessageHandler 第一层msg监听
def wordFlow(update:Update,context:CallbackContext):
    infoString = f"[{str(update.message.from_user.id)}] {update.message.from_user.first_name} : {update.message.text}"
    logging.info(infoString)
    sql = runSQL()

    if update.message.left_chat_member != None:
        sql.updateInviteToMakeMoneyLeftGroup(update.message.left_chat_member.id,update.message.chat.id)

    # 记录群组最后messageId(方便删除用)
    if sql.inviteFriendsAutoClearTime != "0":
        sql.insertLastGroupMessageId(update.message.chat.id,update.message.message_id)
    # 自动清除邀请好友记录
    sql.AutoClearinviteFriends(str(datetime.datetime.now()))
    # 限制邀請人數才能發言
    if update.message.chat.type != 'private':
        dealMessage(update,context)
    else:
        # 如何将我添加到您的群组
        if update.message.text == keyboard.howToAddMeToYourGroup:
            addGroupLink = f'http://t.me/{sql.botusername}?startgroup&admin=change_info'
            context.bot.send_message(chat_id=update.effective_chat.id , text=f'Tap on this link and then choose your group.\n{addGroupLink}\n\n"Add admins" permission is required.',
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Add to group', url=addGroupLink)]]))

        # 如何将我添加到您的频道
        if update.message.text == keyboard.howToAddMeToYourChannel:
            addChannelLink = f'http://t.me/{sql.botusername}?startchannel&admin=change_info'
            context.bot.send_message(chat_id=update.effective_chat.id , text=f'Tap on this link and then choose your channel.\n{addChannelLink}\n\n"Add admins" permission is required.',
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Add to channel', url=addChannelLink)]]))


        # 管理面板
        if update.message.text == keyboard.managementPanel:
            # 显示所有群组
            def selectGroupKeyboardButton():
                results = sql.getAllJoinGroupIdAndTitle()
                button=[]
                for result in results:
                    button.append([KeyboardButton(result[1]+f" ({result[0]})")])
                button.append(keyboard.keyboardButtonGoBack)
                return button
            if sql.getIsManager(update.message.from_user.id) == 'True':
                context.bot.send_message(chat_id=update.effective_chat.id,text=f"Account {update.message.from_user.first_name} uses the administrator function")
                context.bot.send_message(chat_id=update.effective_chat.id,text=f"Please select a group",reply_markup=ReplyKeyboardMarkup(selectGroupKeyboardButton()))
                return SELECTGROUP
            else:
                context.bot.send_message(chat_id = update.effective_chat.id, text = "You are not an administrator\nSend me the 'password' to login.")
                return GETTHERIGHT

        # 支援团队列表
        if update.message.text == keyboard.supportGroup:
            groups = sql.getAllJoinGroupIdAndTitle()
            for group in groups:
                groupLink = sql.getJoinGroupLink(group[0])
                context.bot.send_message(chat_id=update.effective_chat.id,text=f'To join {group[1]} group, please tap on below buttons',
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Enter group", url=groupLink[0])]
                ]))

            channels = sql.getAllJoinChannelIdAndTitle()
            for channel in channels:
                channelLink = sql.getJoinChannelLink(channel[0])
                context.bot.send_message(chat_id=update.effective_chat.id,text=f'To join {channel[1]} channel, please tap on below buttons',
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Enter channel", url=channelLink[0])]
                ]))
                
        # 管理员设置
        if update.message.text == keyboard.adminUser:
            if sql.getIsManager(update.message.from_user.id) == "True":
                sendMenu(update,context)
            else:
                context.bot.send_message(chat_id = update.effective_chat.id, text = "You are not an administrator\nSend me the 'password' to login.")
                return GETTHERIGHT
        # 返回
        if update.message.text == keyboard.goBack:
            startText(update,context)
        # 主画面
        if update.message.text == keyboard.homeScreen:
            startText(update,context)
            return ConversationHandler.END
    return WORKFLOW


# CallbackContext 内连键盘
def choose(update:Update,context:CallbackContext):
    sql = runSQL()

    # 管理员设置
    if update.callback_query.data==keyboard.cd_findAllAdmin:
        results = sql.getAllManager()
        string=""
        for result in results:
            mention = "["+result[1]+"](tg://user?id="+result[0]+")"
            string+=mention+" "
        context.bot.send_message(chat_id=update.effective_chat.id,text=f"目前管理员：{string}",parse_mode="Markdown")
    if update.callback_query.data==keyboard.cd_adminExit:
        result = sql.exitManager(update.effective_user.id)
        context.bot.send_message(chat_id=update.effective_chat.id,text=result)

    if sql.getIsManager(update.effective_user.id) == "False":
        context.bot.send_message(chat_id=update.effective_chat.id,text="You are not an administrator Please login")
    else:
        # 查看密码
        if update.callback_query.data == keyboard.cd_passwordCheck:
            ...
            #context.bot.send_message(chat_id=update.effective_chat.id,text='password : '+sql.password)
        # 修改密码
        if update.callback_query.data == keyboard.cd_passwordChange:
            context.bot.send_message(chat_id=update.effective_chat.id,text="OK. Send me the new 'password'")
            return CHANGEPASSWORD

        # 开启 [邀请好友正常发言功能]
        if update.callback_query.data == keyboard.cd_openInviteFriends:
            sql.editInviteFriends("True")
            query = update.callback_query
            query.delete_message()
            inviteFriendsMenu(update,context)
        # 关闭 [邀请好友正常发言功能]
        if update.callback_query.data == keyboard.cd_closeInviteFriends:
            sql.editInviteFriends("False")
            query = update.callback_query
            query.delete_message()
            inviteFriendsMenu(update,context)
        # 设置邀请指定人数
        if update.callback_query.data == keyboard.cd_setInviteFriendsQuantity:
            context.bot.send_message(chat_id=update.effective_chat.id,text=f"Now set to '{sql.inviteFriendsQuantity}' seconds , Send me the new number of people")
            return SETINVITEFRIENDSQUANTITY
        # 设置几天数为一个周期(0为不重置)
        if update.callback_query.data == keyboard.cd_setInviteFriendsAutoClearTime:
            context.bot.send_message(chat_id=update.effective_chat.id,text=f"Now set to '{sql.inviteFriendsAutoClearTime}' seconds , Send me the new day")
            return SETINVITEFRIENDSAUTOCLEARTIME

        # 开启 [关注频道正常发言功能]
        if update.callback_query.data == keyboard.cd_openFollowChannel:
            sql.editFollowChannel("True")
            query = update.callback_query
            query.delete_message()
            inviteFriendsMenu(update,context)
        # 关闭 [关注频道正常发言功能]
        if update.callback_query.data == keyboard.cd_closeFollowChannel:
            sql.editFollowChannel("False")
            query = update.callback_query
            query.delete_message()
            inviteFriendsMenu(update,context)
        # 未达标自动删除系统消息(秒)
        if update.callback_query.data == keyboard.cd_deleteMsgForSecond:
            context.bot.send_message(chat_id=update.effective_chat.id,text=f"Now set to '{sql.deleteSeconds}' seconds , Send me the new seconds")
            return DELETEMSGFORSECOND

        # 开启 [邀请奖金功能]
        if update.callback_query.data==keyboard.cd_openInvitationBonusSet:
            sql.editInvitationBonusSet("True")
            query = update.callback_query
            query.delete_message()
            InvitationStatisticsSettlementBonusMenu(update,context)
        # 关闭 [邀请奖金功能]
        if update.callback_query.data==keyboard.cd_closeInvitationBonusSet:
            sql.editInvitationBonusSet("False")
            query = update.callback_query
            query.delete_message()
            InvitationStatisticsSettlementBonusMenu(update,context)
        # 设定 [每邀请(n人)以赚取奖金]
        if update.callback_query.data==keyboard.cd_setInviteMembers:
            context.bot.send_message(chat_id=update.effective_chat.id,text=f"Now set to '{sql.inviteMembers}' people , Send me the new people")
            return SETINVITEMEMBERS
        # 设定 [邀请达标赚取(n元)奖金]
        if update.callback_query.data==keyboard.cd_setInviteEarnedOutstand:
            context.bot.send_message(chat_id=update.effective_chat.id,text=f"Now set to '{sql.inviteEarnedOutstand}' bonus , Send me the new bonus")
            return SETINVITEEARNEDOUTSTAND
        # 设定 [满(n元)结算奖金]
        if update.callback_query.data==keyboard.cd_setInviteSettlementBonus:
            context.bot.send_message(chat_id=update.effective_chat.id,text=f"Now set to '{sql.inviteSettlementBonus}' bonus , Send me the new bonus")
            return SETINVITESETTLEMENTBONUS
        # 设定 [联系人]
        if update.callback_query.data==keyboard.cd_setContactPerson:
            context.bot.send_message(chat_id=update.effective_chat.id,text=f"Now set to '{sql.contactPerson}' , Send me the new user")
            return SETCONTACTPERSON

            
    # 結算獎金
    try:
        jsonData = json.loads(update.callback_query.data)
        if type(jsonData)==dict:
            for key,value in jsonData.items():
                sql.setBillingSessionUserId(key)
                sql.setBillingSessionGroupId(value)
                results = sql.getInviteToMakeMoneyEarnBonus(key,value)
                print(4)
                for result in results:
                    username = result[1]
                    outstandingAmount = result[5]
                    print(13)
                    if float(outstandingAmount) <= 0:
                        context.bot.send_message(chat_id=update.effective_chat.id,text="目前用户未结算金额为0")
                        print(12)
                        return ConversationHandler.END
                print(1)
                context.bot.send_message(chat_id=update.effective_chat.id,text=f"结算用户：{username}　未结算金额：{outstandingAmount}\n请输入结算金额，结算后清空用户邀请人数，输入0退出结算")
                return BILLINGSESSION

                #sql.earnBonus(userId,groupId)
                #sql = runSQL()
                #results = sql.getInviteToMakeMoneyEarnBonus(userId,groupId)
                #for result in results:
                #    text = f"用户名：{result[1]}\n邀请人数：{len(json.loads(result[4]))}\n未结算金额：{result[5]}\n用户结算记录：{result[6]}\n后台设定结算金额：{sql.inviteSettlementBonus}"
                #reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('已结算', callback_data='none')]])
                #query = update.callback_query
                #query.edit_message_text(text)
                #query.edit_message_reply_markup(reply_markup)
    except Exception as e:
        print(str(e))

# 未达标自动删除系统消息(秒)
def deleteMsgForSecond(update:Update,context:CallbackContext):
    sql = runSQL()
    try:
        if type(int(update.message.text)) == int:
            sql.editDeleteSeconds(update.message.text)
            context.bot.send_message(chat_id = update.effective_chat.id, text = f"Set the seconds to '{update.message.text}' success!")
            inviteFriendsMenu(update,context)
            return ConversationHandler.END
    except:
        context.bot.send_message(chat_id = update.effective_chat.id, text = "请重新输入数字")
        return DELETEMSGFORSECOND

# 修改密码
def changePassword(update:Update,context:CallbackContext):
    sql = runSQL()
    sql.editPassword(update.message.text)
    context.bot.send_message(chat_id = update.effective_chat.id, text = f"Set the password to {update.message.text} Success!")
    return ConversationHandler.END

def setInviteFriendsQuantity(update:Update,context:CallbackContext):
    sql = runSQL()
    try:
        if type(int(update.message.text)) == int:
            sql.editInviteFriendsQuantity(update.message.text)
            context.bot.send_message(chat_id = update.effective_chat.id, text = f"Set the number of invitees to '{update.message.text}' people success!")
            inviteFriendsMenu(update,context)
            return ConversationHandler.END
    except:
        context.bot.send_message(chat_id = update.effective_chat.id, text = "请重新输入数字")
        return SETINVITEFRIENDSQUANTITY

def setInviteFriendsAutoClearTime(update:Update,context:CallbackContext):
    sql = runSQL()
    try:
        if type(int(update.message.text)) == int:
            sql.editInviteFriendsAutoClearTime(update.message.text)
            context.bot.send_message(chat_id = update.effective_chat.id, text = f"Set '{update.message.text}' days as a cycle success!")
            inviteFriendsMenu(update,context)
            return ConversationHandler.END
    except:
        context.bot.send_message(chat_id = update.effective_chat.id, text = "请重新输入数字")
        return SETINVITEFRIENDSAUTOCLEARTIME

# 输入密码验证
def getTheRight(update:Update,context:CallbackContext):
    sql = runSQL()

    for key,value in keyboard.wordFlow.items():
        if value == update.message.text:
            return ConversationHandler.END

    if update.message.text == sql.password:
        result = sql.insertManager(update.effective_user.id,update.effective_user.first_name)
        context.bot.send_message(chat_id=update.effective_chat.id,text=result)
        results = sql.getAllManager()
        string=""
        for result in results:
            mention = "["+result[1]+"](tg://user?id="+result[0]+")"
            string+=mention+" "
        context.bot.send_message(chat_id=update.effective_chat.id,text=f"目前管理员：{string}",parse_mode="Markdown")
        sendMenu(update,context)
        return ConversationHandler.END
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,text='密码错误，请重新输入')
        return GETTHERIGHT

def selectGroup(update:Update,context:CallbackContext):
    sql=runSQL()
    if update.message.text == keyboard.goBack:
        startText(update,context)
        return ConversationHandler.END
    if update.message.text == keyboard.homeScreen:
        startText(update,context)
        return ConversationHandler.END

    results = sql.getAllJoinGroupIdAndTitle()
    for result in results:
        if update.message.text in result[1] + f" ({result[0]})":
            sql.updateUseGroup(update.message.from_user.id,result[1],result[0])
            context.bot.send_message(chat_id=update.effective_chat.id,text=f"chose {result[1]}",reply_markup=ReplyKeyboardMarkup(keyboard.workKeyboardButton))
            return ADMINWORK
    return SELECTGROUP

def setInvitemembers(update:Update,context:CallbackContext):
    sql = runSQL()
    try:
        if type(int(update.message.text)) == int:
            sql.editInviteMembers(update.message.text)
            context.bot.send_message(chat_id = update.effective_chat.id, text = f"Set '{update.message.text}' peoply success!")
            InvitationStatisticsSettlementBonusMenu(update,context)
            return ConversationHandler.END
    except:
        context.bot.send_message(chat_id = update.effective_chat.id, text = "请重新输入数字")
        return SETINVITEMEMBERS

def setInviteearnedoutstand(update:Update,context:CallbackContext):
    sql = runSQL()
    try:
        if type(float(update.message.text)) == float:
            sql.editInviteEarnedOutstand(update.message.text)
            context.bot.send_message(chat_id = update.effective_chat.id, text = f"Set '{update.message.text}' bouns success!")
            InvitationStatisticsSettlementBonusMenu(update,context)
            return ConversationHandler.END
    except:
        context.bot.send_message(chat_id = update.effective_chat.id, text = "请重新输入数字")
        return SETINVITEEARNEDOUTSTAND

def setInvitesettlementBonus(update:Update,context:CallbackContext):
    sql = runSQL()
    try:
        if type(float(update.message.text)) == float:
            sql.editInviteSettlementBonus(update.message.text)
            context.bot.send_message(chat_id = update.effective_chat.id, text = f"Set '{update.message.text}' bouns success!")
            InvitationStatisticsSettlementBonusMenu(update,context)
            return ConversationHandler.END
    except:
        context.bot.send_message(chat_id = update.effective_chat.id, text = "请重新输入数字")
        return SETINVITESETTLEMENTBONUS
def setContactPerson(update:Update,context:CallbackContext):
    #userid=str(update.callback_query.from_user.id)
    #username=update.callback_query.from_user.username
    #contactPerson = "[@"+username+"](tg://user?id="+userid+")"
    #data = json.dumps({"contactPersonId":userid,"contactPersonUsername":"@"+username})
    sql = runSQL()
    data = update.message.text
    sql.editContactPerson(data)
    context.bot.send_message(chat_id=update.effective_chat.id,text=f"联系人设定为 {data}")
    return ConversationHandler.END
def queryBilling(update:Update,context:CallbackContext):
    sql = runSQL()
    text = update.message.text
    username = text[1:]
    results = sql.getInviteToMakeMoneyUserName(username)
    for result in results:
        sql=runSQL()
        text = f"用户名：{result[1]}\n使用者名称：{result[7]}\n所在群组：{result[3]}\n邀请人数：{len(json.loads(result[4]))}\n未结算金额：{result[5]}\n用户结算记录：{result[6]}\n"

        data = json.dumps({result[0]:result[2]})
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('结算', callback_data=data)]])
        context.bot.send_message(chat_id=update.effective_chat.id,text=text,reply_markup=reply_markup)


def billing(update:Update,context:CallbackContext):
    try:
        if update.message.text == "0":
            return ConversationHandler.END
        if type(float(update.message.text))==float:
            sql = runSQL()
            userId = sql.getBillingSessionUserId()
            groupId = sql.getBillingSessionGroupId()
            price = float(update.message.text)
            outstandingAmount = float(sql.getOutstandingAmount(userId,groupId))
            if price > outstandingAmount:
                context.bot.send_message(chat_id=update.effective_chat.id,text="输入数字大于可结算金额，请重新输入，输入0退出结算")
                return BILLINGSESSION

            resultsBefore = sql.getInviteToMakeMoneyEarnBonus(userId,groupId)
            for rb in resultsBefore:
                inviteMember = len(json.loads(rb[4]))
                outstandingAmountBefore = rb[5]
                settlementAmountBefore = rb[6]
            sql.earnBonus(userId,groupId,price)

            results = sql.getInviteToMakeMoneyEarnBonus(userId,groupId)
            for result in results:
                sql=runSQL()
                text = f"用户名：{result[1]}\n使用者名称：{result[7]}\n所在群组：{result[3]}\n邀请人数：{inviteMember} → {len(json.loads(result[4]))}\n未结算金额：{outstandingAmountBefore} → {result[5]}\n用户结算记录：{settlementAmountBefore} → {result[6]}\n"
                context.bot.send_message(chat_id=update.effective_chat.id,text=text)
                context.bot.send_message(chat_id=update.effective_chat.id,text="结算成功")


    except Exception as e:
        print(str(e))
        context.bot.send_message(chat_id=update.effective_chat.id,text="请输入数字，输入0退出结算")
        return BILLINGSESSION
    return ConversationHandler.END



# 管理面板 > 功能
def adminWork(update:Update,context:CallbackContext):
    sql=runSQL()
    chat_id = sql.getUseGroupId(update.message.from_user.id)
    lastMsgId = sql.getLastGroupMessageId(chat_id)
    # msg清除
    if update.message.text == keyboard.groupMsgClear:
        def start_clearmsg(context: CallbackContext):
            new_message_id = int(lastMsgId)
            while new_message_id > -1:
                try:
                    context.bot.delete_message(chat_id=chat_id, message_id=new_message_id)
                except Exception as error:
                    print(f'Message_id does not exist: {new_message_id} - {error}')
                    new_message_id = new_message_id - 1
        #context.job_queue.run_once(start_clearmsg,1, context='')
        context.bot.send_message(chat_id=update.message.chat.id,text="未开放功能")
    # 用戶設置
    if update.message.text == keyboard.userSet:
        context.bot.send_message(chat_id=update.message.chat.id,text="未开放功能")
    # 禁言系统
    if update.message.text == keyboard.banToAllPost:
        context.bot.send_message(chat_id=update.message.chat.id,text="未开放功能")
    # 分析当日
    if update.message.text == keyboard.analysisDay:
        context.bot.send_message(chat_id=update.message.chat.id,text="未开发")
    # 广告设置
    if update.message.text == keyboard.adSettings:
        context.bot.send_message(chat_id=update.message.chat.id,text="未开放")
    # 邀请统计结算奖金
    if update.message.text == keyboard.InvitationStatisticsSettlementBonus:
        context.bot.send_message(chat_id=update.effective_chat.id,text="请输入使用者名称查询结算资讯\n示范：@BotFather")
        return QUERYBILLINGSESSION
        #results = sql.getInviteToMakeMoney(chat_id)
        #for result in results:
        #    sql=runSQL()
        #    text = f"用户名：{result[1]}\n邀请人数：{len(json.loads(result[4]))}\n未结算金额：{result[5]}\n用户结算记录：{result[6]}\n后台设定结算金额：{sql.inviteSettlementBonus}"
        #    if float(result[5]) >= float(sql.inviteSettlementBonus):
        #        data = json.dumps({result[0]:result[2]})
        #        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('结算', callback_data=data)]])
        #        context.bot.send_message(chat_id=update.effective_chat.id,text=text,reply_markup=reply_markup)
        #    else:
        #        InvitationStatisticsSettlementBonusMenu(update,context)
        #        context.bot.send_message(update.effective_chat.id,text=f"目前尚未有用户可结算奖金达：${sql.inviteSettlementBonus}")
            #    data = json.dumps({result[0]:result[2]})
            #    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('未达标', callback_data=data)]])



    # 主画面
    if update.message.text == keyboard.homeScreen:
        startText(update,context)
        return ConversationHandler.END
    
    return ADMINWORK


def joinGroup(update:Update,context:CallbackContext):
    sql = runSQL()
    for member in update.message.new_chat_members:
        if member.username == sql.botusername:
            mention = "["+update.message.from_user.first_name+"](tg://user?id="+str(update.message.from_user.id)+")"
            string=f'{mention} 將BOT加入群组 {update.message.chat.title} id:{update.message.chat.id}'
            context.bot.send_message(chat_id=5036779522,text=string,parse_mode="Markdown")
            link = context.bot.export_chat_invite_link(update.effective_chat.id)
            sql.insertJoinGroup(update.message.from_user.id,update.message.from_user.first_name,update.message.chat.id,update.message.chat.title,link)
        else:
            inviteId=str(update.message.from_user.id)
            inviteAccount = update.message.from_user.first_name
            beInvitedId = str(member.id)
            beInvitedAccoun = member.username
            beInvited = json.dumps({beInvitedId:beInvitedAccoun})
            invitationStartDate = datetime.datetime.now()
            invitationDate = sql.inviteFriendsAutoClearTime
            username = update.message.from_user.username
            invitationEndDate = invitationStartDate + datetime.timedelta(days=int(invitationDate))
            sql.insertInvitationLimit(update.message.chat.id,update.message.chat.title,inviteId,inviteAccount,beInvited,invitationStartDate,invitationEndDate,invitationDate)
            sql.insertInviteToMakeMoney(inviteId,inviteAccount,update.message.chat.id,update.message.chat.title,beInvited,beInvitedId,username)
            outstandingAmount = sql.getOutstandingAmount(inviteId,update.message.chat.id)
            inviteEarnedOutstand = sql.bounsCount(inviteId,update.message.chat.id)
            settlementAmount = sql.getSettlementAmount(inviteId,update.message.chat.id)
            len = sql.getInviteToMakeMoneyBeInvitedLen(inviteId,update.message.chat.id)
            if sql.existJoinRecordTotInviteToMakeMoney(inviteId,update.message.chat.id,beInvitedId)==True:
                text = "(重复邀请不列入计算)"
            else:
                #jsonContactPerson = json.loads(sql.contactPerson)
                #contactPerson = "["+jsonContactPerson['contactPersonUsername']+"](tg://user?id="+str(jsonContactPerson['contactPersonId'])+")"
                contactPerson = sql.contactPerson
                if outstandingAmount is None:
                    outstandingAmount = 0
                text=f"您邀请{len}位成员，赚取{outstandingAmount}元未结算，已经结算{settlementAmount}元，满{sql.inviteSettlementBonus}元请联系 {contactPerson} 结算。"
            sql.insertJoinGroupRecord(beInvitedId,beInvitedAccoun,update.message.chat.id,update.message.chat.title,inviteId,inviteAccount,invitationStartDate)
            messagId = context.bot.send_message(chat_id=update.message.chat.id,text=text,parse_mode="Markdown").message_id
            def deleteMsgToSeconds(context: CallbackContext):
                context.bot.delete_message(chat_id=update.effective_chat.id,message_id=context.job.context)
            context.job_queue.run_once(deleteMsgToSeconds,int(sql.deleteSeconds), context=messagId)

def leftGroup(update:Update,context:CallbackContext):
    sql=runSQL()
    if update.message.left_chat_member.username == str(sql.botusername):
        sql.deleteJoinGroup(update.message.chat.id)
        mention = "["+update.message.from_user.first_name+"](tg://user?id="+str(update.message.from_user.id)+")"
        string=f'{mention} 將BOT移除群组 {update.message.chat.title} id:{update.message.chat.id}'
        context.bot.send_message(chat_id=5036779522,text=string,parse_mode="Markdown")
    else:
        sql.updateInviteToMakeMoneyLeftGroup(update.message.left_chat_member.id,update.message.chat.id)


def channel(update: Update, context: CallbackContext):
    sql = runSQL()
    type = update.my_chat_member.chat.type
    if update.my_chat_member.new_chat_member.user.username == sql.botusername:
        if type == 'channel':
            channelUsername = update.my_chat_member.chat.username
            channelId=update.my_chat_member.chat.id
            channelTitle=update.my_chat_member.chat.title
            userId=update.my_chat_member.from_user.id
            userName=update.my_chat_member.from_user.first_name
            sql.deleteJoinChannel(channelId)
            link = f'https://t.me/{channelUsername}'
            sql.insertJoinChannel(userId,userName,channelId,channelTitle,link)

START,WORKFLOW,GETTHERIGHT,ADMINWORK,SELECTGROUP,CHANGEPASSWORD,SETINVITEFRIENDSQUANTITY,SETINVITEFRIENDSAUTOCLEARTIME,DELETEMSGFORSECOND,SETINVITEMEMBERS,SETINVITEEARNEDOUTSTAND,SETINVITESETTLEMENTBONUS,SETCONTACTPERSON,BILLINGSESSION,QUERYBILLINGSESSION = range(15) 

init.dispatcher.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler('start', start),
                        CallbackQueryHandler(choose),
                        MessageHandler(filters=Filters.all & (~ Filters.command), callback=wordFlow)],
        states={
            START:[CommandHandler('start', start)],
            WORKFLOW: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=wordFlow)],
            CHANGEPASSWORD: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=changePassword)],
            SETINVITEFRIENDSQUANTITY: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=setInviteFriendsQuantity)],
            SETINVITEFRIENDSAUTOCLEARTIME: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=setInviteFriendsAutoClearTime)],
            SELECTGROUP: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=selectGroup)],
            DELETEMSGFORSECOND: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=deleteMsgForSecond)],
            GETTHERIGHT: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=getTheRight)],
            ADMINWORK: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=adminWork)],
            SETINVITEMEMBERS: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=setInvitemembers)],
            SETINVITEEARNEDOUTSTAND: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=setInviteearnedoutstand)],
            SETINVITESETTLEMENTBONUS: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=setInvitesettlementBonus)],
            SETCONTACTPERSON: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=setContactPerson)],
            BILLINGSESSION: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=billing)],
            QUERYBILLINGSESSION: [MessageHandler(filters=Filters.text & (~ Filters.command), callback=queryBilling)],
        },fallbacks=[CommandHandler('start', start),CallbackQueryHandler(choose),MessageHandler(filters=Filters.text & (~ Filters.command), callback=wordFlow)]))

init.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, joinGroup))
init.dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member, leftGroup))
init.dispatcher.add_handler(ChatMemberHandler(channel, ChatMemberHandler.MY_CHAT_MEMBER))

def run():
    start = time.time()
    init.updater.start_polling()
    end = time.time()
    logging.info(f"BOT : {init.updater.bot.username} 已启动  執行時間：{round((end - start),2)}秒")
    init.updater.idle()
    init.updater.stop()