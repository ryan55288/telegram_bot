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
log_directory = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))+"\log"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

logging.basicConfig(level=logging.DEBUG,
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
    invitationBonusSetText = f"目前状态：{invitationBonusSet}\n邀请人数：{sql.inviteMembers}\n获得奖金：{sql.inviteEarnedOutstand}\n结算奖金：{sql.inviteSettlementBonus}"
    context.bot.send_message(chat_id = update.effective_chat.id,text=invitationBonusSetText,reply_markup = keyboard.InvitationStatisticsSettlementBonusMenu)

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
    mention = "["+first_name+"](tg://user?id="+str(update.message.from_user.id)+")"
    len = sql.getDynamicInviteFriendsQuantity(update.message.from_user.id)

    def catchChannel():
        try:
            update.message.reply_to_message.forward_from_chat.type
            return True
        except AttributeError:
            return False
            
    def deleteMsgToSeconds(context: CallbackContext):
        context.bot.delete_message(chat_id=update.effective_chat.id,message_id=context.job.context)

    if sql.getIsManager(update.effective_user.id) == "False" or sql.getManager(update.effective_user.id) is None:
        if sql.getInviteFriendsSet() == "True":
            if first_name != "Telegram":
                if catchChannel() == False:
                    if sql.messageLimitToInviteFriends(update.message.from_user.id,update.message.chat.id) == False:
                        context.bot.delete_message(chat_id=update.effective_chat.id,message_id=update.message.message_id)
                        messagea = context.bot.send_message(chat_id=update.effective_chat.id,text=f"{mention}：您需要邀请{len}位好友后可以正常发言",parse_mode="Markdown").message_id
                        context.job_queue.run_once(deleteMsgToSeconds,int(sql.deleteSeconds), context=messagea)
        try:
            if context.bot.get_chat_member(int(sql.getChannelId()[0]),update.effective_user.id).status =="left":
                if sql.getFollowChannelSet() == "True":
                    channelmark = "[@"+sql.channelLink[13:]+"]("+sql.channelLink+")"
                    messagec = context.bot.send_message(chat_id=update.effective_chat.id,text=f"{mention}：您需关注频道{channelmark}后可以正常发言",parse_mode="Markdown").message_id
                    context.job_queue.run_once(deleteMsgToSeconds,int(sql.deleteSeconds), context=messagec)
        except Exception as e:
            print("機器人尚未加入頻道"+str(e))
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
        # 邀请统计结算奖金
        if update.message.text == keyboard.InvitationStatisticsSettlementBonus:
            if sql.getIsManager(update.message.from_user.id) == "True":
                results = sql.getInviteToMakeMoney(update.message.chat.id)
                print(results)
                for result in results:
                    print(111)
                    text = f"用户名:{result[1]} 邀请{len(json.loads(result[4]))}人 未结算金额:{result[5]} 总结算金额:{result[6]}"
                    print(111)
                    context.bot.send_message(chat_id=update.message.chat.id,text=text)
                    
                context.bot.send_message(chat_id=update.message.chat.id,text=keyboard.InvitationStatisticsSettlementBonus)
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
            context.bot.send_message(chat_id=update.effective_chat.id,text='password : '+sql.password)
        # 修改密码
        if update.callback_query.data == keyboard.cd_passwordChange:
            context.bot.send_message(chat_id=update.effective_chat.id,text="OK. Send me the new 'password'")
            return CHANGEPASSWORD

        # 开启 [邀请好友正常发言功能]
        if update.callback_query.data == keyboard.cd_openInviteFriends:
            sql.editInviteFriends("True")
            inviteFriendsMenu(update,context)
        # 关闭 [邀请好友正常发言功能]
        if update.callback_query.data == keyboard.cd_closeInviteFriends:
            sql.editInviteFriends("False")
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
        # 关闭 [关注频道正常发言功能]
        if update.callback_query.data == keyboard.cd_closeFollowChannel:
            sql.editFollowChannel("False")
        # 未达标自动删除系统消息(秒)
        if update.callback_query.data == keyboard.cd_deleteMsgForSecond:
            context.bot.send_message(chat_id=update.effective_chat.id,text=f"Now set to '{sql.deleteSeconds}' seconds , Send me the new seconds")
            return DELETEMSGFORSECOND

        # 开启 [邀请奖金功能]
        if update.callback_query.data==keyboard.cd_openInvitationBonusSet:
            sql.editInvitationBonusSet("True")
            InvitationStatisticsSettlementBonusMenu(update,context)
        # 关闭 [邀请奖金功能]
        if update.callback_query.data==keyboard.cd_closeInvitationBonusSet:
            sql.editInvitationBonusSet("False")
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

# 未达标自动删除系统消息(秒)
def deleteMsgForSecond(update:Update,context:CallbackContext):
    sql = runSQL()
    try:
        if type(int(update.message.text)) == int:
            sql.editDeleteSeconds(update.message.text)
            context.bot.send_message(chat_id = update.effective_chat.id, text = f"Set the seconds to '{update.message.text}' success!")
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
        context.bot.send_message(chat_id=update.message.chat.id,text="开发中")


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
            invitationEndDate = invitationStartDate + datetime.timedelta(days=int(invitationDate))
            sql.insertInvitationLimit(update.message.chat.id,update.message.chat.title,inviteId,inviteAccount,beInvited,invitationStartDate,invitationEndDate,invitationDate)
            sql.insertInviteToMakeMoney(inviteId,inviteAccount,update.message.chat.id,update.message.chat.title,beInvited,beInvitedId)
            
            inviteEarnedOutstand = sql.bounsCount(inviteId,update.message.chat.id)
            settlementAmount = sql.getSettlementAmount(inviteId,update.message.chat.id)
            len = sql.getInviteToMakeMoneyBeInvitedLen(inviteId,update.message.chat.id)
            if sql.existJoinRecordTotInviteToMakeMoney(inviteId,update.message.chat.id,beInvitedId)==True:
                text = "(重复邀请不列入计算)"
            else:
                a = "@kk"
                b = 5036779522
                mention = "["+a+"](tg://user?id="+str(b)+")"
                text=f"您邀请{len}位成员，赚取{inviteEarnedOutstand}元未结算，已经结算{settlementAmount}元，满{sql.inviteSettlementBonus}元请联系{mention}结算。"
            sql.insertJoinGroupRecord(beInvitedId,beInvitedAccoun,update.message.chat.id,update.message.chat.title,inviteId,inviteAccount,invitationStartDate)
            context.bot.send_message(chat_id=update.message.chat.id,text=text,parse_mode="Markdown")


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

START,WORKFLOW,GETTHERIGHT,ADMINWORK,SELECTGROUP,CHANGEPASSWORD,SETINVITEFRIENDSQUANTITY,SETINVITEFRIENDSAUTOCLEARTIME,DELETEMSGFORSECOND,SETINVITEMEMBERS,SETINVITEEARNEDOUTSTAND,SETINVITESETTLEMENTBONUS = range(12) 

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
        },fallbacks=[CommandHandler('start', start),CallbackQueryHandler(choose),MessageHandler(filters=Filters.text & (~ Filters.command), callback=wordFlow)]))

init.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, joinGroup))
init.dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member, leftGroup))
init.dispatcher.add_handler(ChatMemberHandler(channel, ChatMemberHandler.MY_CHAT_MEMBER))

def run():
    init.updater.start_polling()
    init.updater.idle()
    init.updater.stop()