import datetime
import json
import logging
import os
import random
import time

import requests

from gong_xue_yun import getSign, doLogin, getPlanIdSign, getPlanId, getDailySign, getT

logger = logging.getLogger()

logData = []

loginURL = "https://api.moguding.net:9000/session/user/v3/login"
# doCardURL = "https://api.moguding.net:9000/attendence/clock/v4/save"
planIdURL = "https://api.moguding.net:9000/practice/plan/v3/getPlanByStu"
dailyURL = "https://api.moguding.net:9000/practice/paper/v5/save"
ReplaceURL = "https://api.moguding.net:9000/attendence/attendancee/v4/save"

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
    "Accept-Encoding": "gzip",
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


def doCard(data):
    cardData = {
        "address": data.get("address"),
        "city": data.get("city"),
        "area": data.get("area"),
        "country": data.get("country"),
        "createTime": data.get("random_time"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "province": data.get("province"),
        "state": "NORMAL",
        "type": data.get("cardType"),
        "planId": data.get("planId"),
        "attendanceType": "REPLACE",
        "userId": data.get("userId"),
        "t": getT()
    }
    headers["sign"] = data.get("sign")
    headers["Authorization"] = data.get("token")
    doCardResult = requests.post(ReplaceURL, headers=headers, data=json.dumps(cardData)).json()
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
        errorLog = data.get("account") + doCardResult["msg"] + time.strftime("%Y-%m-%d -- %H:%M:%S", time.localtime())
        logData.append(errorLog)


def doDaily(data):
    random_time_str = data["random_time"]
    random_time = datetime.datetime.strptime(random_time_str, "%Y-%m-%d %H:%M:%S")

    # 创建新的datetime对象用于设置"current_date"
    current_date = datetime.datetime(
        random_time.year, random_time.month, random_time.day, random_time.hour, random_time.minute, random_time.second
    )  # 初始时间设定为从txt文件中读取的时间

    # 模拟时间流逝，每次循环增加一天
    current_date += datetime.timedelta(days=1)

    # 生成随机时间
    random_hour = random.randint(0, 23)
    random_minute = random.randint(0, 59)
    random_second = random.randint(0, 59)

    random_time = current_date.replace(hour=random_hour, minute=random_minute, second=random_second)
    # print(random_time)
    data["random_time"] = random_time.strftime("%Y-%m-%d %H:%M:%S")


    def get_daily_data(title, report_type):
        print(data.get("random_time"))
        return {
            "t": getT(),
            "title": title,
            "content": content,
            "planId": data.get("planId"),
            "reportType": report_type,
            "reportTime": data.get("random_time")
        }

    def get_headers(title, report_type):
        return {
            "Authorization": data.get("token"),
            "sign": getDailySign(data.get("userId"), report_type, title, data.get("planId"))
        }

    day = int(data.get('day'))
    data["day"] = day + 1
    print("今天是", day, "号")

    data_file = "basic_info/" + data.get('account') + ".json"
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding="utf-8") as f:
            text = json.load(f)
            content = text[int(day) - 1]["content"]
            logData.append(content)
    else:
        with open(r'basic_info/week_diary.json', 'r', encoding="utf-8") as f:
            text = json.load(f)
            content = text[int(day) - 1]["content"]
            print(content)
            logData.append(content)

    daily_data = get_daily_data("日报", "day")
    headers = get_headers("日报", "day")

    do_daily_result = requests.post(dailyURL, headers=headers, json=daily_data)

    print("日报结果是：" + str(do_daily_result.text))


if __name__ == "__main__":
    po = User_PO()
    for _ in range(10):
        po.do()
        print('休息3秒')
        time.sleep(3)
