# coding:utf-8
import datetime
import hashlib
import json
import logging
import os
import time

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

logger = logging.getLogger()

loginURL = "https://api.moguding.net:9000/session/user/v3/login"
doCardURL = "https://api.moguding.net:9000/attendence/clock/v4/save"
planIdURL = "https://api.moguding.net:9000/practice/plan/v3/getPlanByStu"
dailyURL = "https://api.moguding.net:9000/practice/paper/v5/save"

pre = {
    # "http": "http://218.2.214.107:80",
    # "https": "https://http://101.34.59.236:8876"
}

logData = []

headers = {
    "Host": "api.moguding.net:9000",
    "Accept-Language": "zh-CN,zh;q=0.8",
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; Redmi K70 Pro Build/SKQ1.211006.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/117.0.0.0 Mobile Safari/537.36",
    # "User-Agent": "Dart/2.17 (dart:io)",
    "sign": "",
    'Connection': 'keep-alive',
    "Authorization": "",
    "roleKey": "student",
    "Content-Type": "application/json; charset=UTF-8",
    "Accept-Encoding": "",
}


def readFile():
    dataList = []
    # try:
    with open("account.txt", "r+", encoding="UTF-8") as obj:
        readline = obj.readlines()
        for i in readline:
            if i:
                json_loads = json.loads(i)
                dataList.append(json_loads)
            else:
                pass
        return dataList


class User_PO:
    def __init__(self):
        self.userData = readFile()

    def do(self):
        for data in self.userData:
            if data.get("account") is not None and data.get("password") is not None:
                if data.get("state") is not None and data.get("state") == 1:
                    # 上班/下班状态切换
                    data["cardType"] = "END"
                else:
                    data["cardType"] = "START"
                if data.get("token") is not None:
                    # 获得签到的签名
                    sign = getSign(data.get("cardType"), data.get("planId"), data.get("userId"), data.get("address"))
                    data["sign"] = sign
                    doCard(data)
                    doDaily(data)
                else:
                    doLogin(data)
                    if data.get("userId") is None:
                        continue
                    planSign = getPlanIdSign(data["userId"])
                    # //获得planId
                    plan_id = getPlanId(headers, str(data.get("token")), str(planSign))
                    data["planId"] = plan_id
                    # 获得签到的签名
                    sign = getSign(data.get("cardType"), plan_id, data.get("userId"), data.get("address"))
                    data["sign"] = sign
                    doCard(data)
                    doDaily(data)
            else:
                logger.error("请填写账号密码")
        t = open("account.txt", 'w+', encoding="UTF-8")
        writeData = ""
        for data in self.userData:
            writeData = writeData + json.dumps(data, ensure_ascii=False) + "\n"

        t.write(writeData)
        t.close()

        fileName = time.strftime("%Y-%m-%d--%H", time.localtime()) + "打卡日志.txt"
        text_io = open("logs/" + fileName, "w", encoding="UTF-8")
        for line in logData:
            text_io.write(line + "\n")

        text_io.close()


# 登陆
def doLogin(data):
    account_ = encrypt(data.get("account"))
    password_ = encrypt(data.get("password"))
    loginData = {
        "phone": account_,
        "password": password_,
        "loginType": "android",
        "uuid": "",
        "t": getT()
    }
    loginResult = requests.post(loginURL, headers=headers, data=json.dumps(loginData)).json()
    if loginResult["code"] != 200:
        logger.error(loginResult["msg"])
        # pushMessge(data.get("plusToken"), loginResult["msg"])
        errorLog = data.get("account") + loginResult["msg"] + time.strftime("%Y-%m-%d -- %H:%M:%S", time.localtime())
        logData.append(errorLog)
    else:
        # 将获取到的用户信息存入
        data["token"] = str(loginResult["data"]["token"])
        data["userId"] = str(loginResult["data"]["userId"])
        data["moguNo"] = str(loginResult["data"]["moguNo"])


# 推送消息
def pushMessge(token, message):
    hea = {
        "Content-Type": "application/json; charset=UTF-8",
    }
    url = "http://www.pushplus.plus/send"
    requestData = {
        "token": token,
        "title": "学工云出现未知错误！",
        "content": message
    }
    result = requests.post(url, headers=hea, data=json.dumps(requestData)).json()
    print(result)


def bytesToHexString(bs):
    return ''.join(['%02X' % b for b in bs])


# 加密参数
def encrypt(word, key="23DbtQHR2UMbH6mJ"):
    key = key.encode('utf-8')
    mode = AES.MODE_ECB
    aes = AES.new(key, mode)
    pad_pkcs7 = pad(word.encode('utf-8'), AES.block_size, style='pkcs7')  # 选择pkcs7补全
    encrypt_aes = aes.encrypt(pad_pkcs7)
    encrypted_text = bytesToHexString(encrypt_aes)
    return encrypted_text.replace(" ", "").lower()


# 对字符进行加密
def getMd5(byStr):
    encode = byStr.encode('utf-8')
    return hashlib.md5(encode).hexdigest()


def getT():
    t = str(int(time.time()) * 1000)
    return encrypt(t)


# 获取planId的sign
def getPlanIdSign(userId):
    byStr = str(userId) + "student" + "3478cbbc33f84bd00d75d7dfa69e0daa"
    return getMd5(byStr)


# 获取签到sign
def getSign(cardType, planId, userId, address):
    byStr = "Android" + str(cardType) + str(planId) + str(userId) + str(address) + "3478cbbc33f84bd00d75d7dfa69e0daa"
    return getMd5(byStr)


# 获取日报的sign
def getDailySign(userId, reportType, types, planId):
    byStr = str(userId) + reportType + planId + types + "3478cbbc33f84bd00d75d7dfa69e0daa"
    return getMd5(byStr)


# 获得planId
def getPlanId(hea, token, palnIdSign):
    hea["sign"] = palnIdSign
    hea["Authorization"] = token
    hea["roleKey"] = "student"
    data = {
        "state": ""
    }
    planIdResult = requests.post(planIdURL, headers=hea, data=json.dumps(data)).json()
    print(planIdResult)
    return str(planIdResult["data"][0]["planId"])


def doCard(data):
    cardData = {
        "country": data.get("country"),
        "address": data.get("address"),
        "province": data.get("province"),
        "city": data.get("city"),
        "latitude": data.get("latitude"),
        "description": "",
        "planId": data.get("planId"),
        "type": data.get("cardType"),
        "device": "Android",
        "longitude": data.get("longitude"),
    }
    headers["sign"] = data.get("sign")
    headers["Authorization"] = data.get("token")
    doCardResult = requests.post(doCardURL, headers=headers, proxies=pre, data=json.dumps(cardData)).json()
    logger.info(str(doCardResult))
    print("打卡结果是；" + str(doCardResult))
    if doCardResult.get("code") == 200:
        # 切换状态
        if data.get("state") == 1:
            data["state"] = 0
            logger.info(data.get("account") + "下班打卡成功")
        else:
            data["state"] = 1
            logger.info(data.get("account") + "上班打卡成功")
        log = data.get("account") + "打卡成功" + time.strftime("%Y-%m-%d -- %H:%M:%S", time.localtime())
        logData.append(log)
    elif doCardResult.get("code") == 401:
        del data["token"]
        del data["userId"]
        del data["planId"]
        del data["sign"]
        doLogin(data)
        if data.get("userId") is None:
            return
        planSign = getPlanIdSign(data["userId"])
        plan_id = getPlanId(headers, str(data.get("token")), str(planSign))
        data["planId"] = plan_id
        sign = getSign(data.get("cardType"), plan_id, data.get("userId"), data.get("address"))
        data["sign"] = sign
        doCard(data)
    else:
        logger.error(data.get("account") + "打卡失败，未知异常！！")
        pushMessge(data.get("plusToken"), "未知异常，请及时处理！！")
        errorLog = data.get("account") + doCardResult["msg"] + time.strftime("%Y-%m-%d -- %H:%M:%S", time.localtime())
        logData.append(errorLog)


def nowTime():
    current_time = datetime.datetime.now()
    # 格式化时间为指定格式
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    print(formatted_time)
    return formatted_time


def doDaily(data):
    def get_daily_data(title, report_type):
        return {
            "t": getT(),
            "title": title,
            "content": content,
            "planId": data.get("planId"),
            "reportType": report_type,
            "reportTime": nowTime()
        }
    print(getT())

    def get_headers(title, report_type):
        return {
            "Authorization": data.get("token"),
            "sign": getDailySign(data.get("userId"), report_type, title, data.get("planId"))
        }

    current_date = datetime.date.today()
    weekday = current_date.weekday()
    day = current_date.day
    # print("今天是", day, "号")

    data_file = "basic_info/" + data.get('account') + ".json"
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding="utf-8") as f:
            text = json.load(f)
            content = text[int(day) + 26]["content"]
            logData.append(content)
    else:
        with open(r'basic_info/week_diary.json', 'r', encoding="utf-8") as f:
            text = json.load(f)
            content = text[int(day) + 26]["content"]
            logData.append(content)

    daily_data = get_daily_data("日报", "day")
    headers = get_headers("日报", "day")
    # 切换状态
    if data.get("dailyState") == "ok":
        data["dailyState"] = "no"
        print("已经跳过日报请求")
    elif data["dailyState"] == "no":
        data["dailyState"] = "ok"
        do_daily_result = requests.post(dailyURL, headers=headers, json=daily_data)
        # if weekday == 2:
        #     daily_data = get_daily_data("周报", "week")
        #     headers = get_headers("周报", "week")
        #     do_daily_result = requests.post(dailyURL, headers=headers, json=daily_data)
        #     print("周报结果是：" + str(do_daily_result.text))
        # elif day == 15:
        #     daily_data = get_daily_data("月报", "month")
        #     headers = get_headers("月报", "month")
        #     do_daily_result = requests.post(dailyURL, headers=headers, json=daily_data)
        #     print("周报结果是：" + str(do_daily_result.text))

        print("日报结果是：" + str(do_daily_result.text))
    else:
        print("未启动日报功能！")
        pass


if __name__ == "__main__":
    po = User_PO()
    po.do()
