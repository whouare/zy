# [rule: ^(顺风|顺丰)(登录|登陆)$|^登(录|陆)(顺风|顺丰)$|^(顺风|顺丰)(查询|管理)$|^(查询|管理)(顺风|顺丰)$|^顺丰清理$|^顺丰授权$|^顺丰教程$]
# [disable:false]
# [platform: qq,qb,wx,tb,tg,web,wxmp]
# [cron: 56 6,9,13,16,19,20 * * *]
# [public: true]
# [title: 顺丰速运]
# [open_source: false]
# [class: 工具类]
# [version: 6.2]
# [price: 12.88]
# [admin: false]
# [author: linzixuan]
# [service: 2661320550]
# [description: 3.0全新UI<br>介绍：顺丰代挂插件，支持微信扫码登录和CK登录。定时清理授权可添加定时"顺丰清理"<br>更新：增加'清理顺丰'指令<br>更新：查询新增大额优惠卷列表<br>更新：管理员一键授权指令：顺丰授权<br>更新：修复一些小bug<br>更新：适配BOGW和GW框架的收款<br>更新：优化支付处理逻辑<br>更新：修复BOGR和GW框架扫码问题！<br>更新：更新32周年庆勋章卡片查询<br>更新：新增积分状态判断和采蜜活动兑换提醒<br>6.1更新：优化赞赏码支付，同时新增码支付，需使用市场卡密系统！]

import re
from datetime import datetime, timedelta
import middleware
import urllib.parse
from decimal import Decimal
import requests
import time
import json
import hashlib
import urllib.parse
import uuid

senderID = middleware.getSenderID()
# 创建发送者
sender = middleware.Sender(senderID)
# 获取发送者QQ号
userid = sender.getUserID()
# 获取用户的值
uservalue = middleware.bucketGet(bucket='dd_sf_user', key=userid)


# [param: {"required":true,"key":"dd_sf.zsm","bool":false,"placeholder":"必填项,http://xxxx.co/xxx.jpg","name":"收款方式","desc":"Wxbot赞赏码/收款码链接"}]
# [param: {"required":true,"key":"dd_sf.dd_sf_qlname","bool":false,"placeholder":"Host丨ClientID丨ClientSecret","name":"设置对接容器","desc":"你的变量需要添加到的容器？参数用丨分割，这个符号是中文的竖(直接复制)"}]
# [param: {"required":true,"key":"dd_sf.dd_sf_osname","bool":false,"placeholder":"必填项,例:sfsyUrl","name":"提交到青龙的变量名","desc":"青龙容器内顺丰的变量名"}]
# [param: {"required":true,"key":"dd_sf.sfVipmoney","bool":false,"placeholder":"例:0.88,不填为0元","name":"上车价格","desc":"上车价格(单位:元)/月"}]
# [param: {"required":true,"key":"dd_sf.sfcoin","bool":false,"placeholder":"不填为关闭积分支付","name":"积分开通","desc":"授权一个月需要多少积分（只能为整数不能为小数）"}]
# [param: {"required":false,"key":"dd_sf.show_point_status","bool":true,"placeholder":"","name":"显示积分状态","desc":"是否在查询结果中显示积分状态判断"}]
# [param: {"required":true,"key":"dd_sf.use_ma_pay","bool":true,"placeholder":"","name":"使用码支付","desc":"是否使用码支付系统,开启后将使用卡密系统配置的码支付"}]
def getusercontent():
    dd_sf_osname = middleware.bucketGet('dd_sf', 'dd_sf_osname') or 'dd_sf_token'
    dd_sf_qlname = middleware.bucketGet('dd_sf', 'dd_sf_qlname') or 'dd_sf_token'
    dd_managecommand = middleware.bucketGet('dd_sf', 'dd_managecommand') or '顺丰管理'
    dd_querycommand = middleware.bucketGet('dd_sf', 'dd_querycommand') or '顺丰查询'
    dd_signcommand = middleware.bucketGet('dd_sf', 'dd_signcommand') or '顺丰登录'
    dd_tutorialcommand = '顺丰教程'  # 添加教程指令

    # 生成随机指令
    randommanagecommand = dd_managecommand
    randomquerycommand = dd_querycommand
    randomsigncommand = dd_signcommand

    # 获取价格配置
    sfVipmoney = Decimal(middleware.bucketGet('dd_sf', 'sfVipmoney') or '1')
    sfcoin = int(middleware.bucketGet('dd_sf', 'sfcoin') or '0')

    # 获取是否显示积分状态的配置
    show_point_status = middleware.bucketGet('dd_sf', 'show_point_status') or 'false'
    show_point_status = show_point_status.lower() == 'true'

    # 获取是否使用码支付的配置
    use_ma_pay = middleware.bucketGet('dd_sf', 'use_ma_pay') or 'false'
    use_ma_pay = use_ma_pay.lower() == 'true'

    return (dd_sf_osname, dd_sf_qlname, dd_managecommand, dd_querycommand,
            dd_signcommand, randommanagecommand, randomquerycommand,
            randomsigncommand, sfVipmoney, sfcoin, show_point_status, use_ma_pay)


def seekql():
    try:
        if len(dd_sf_qlname) == 0:
            sender.reply("""
=====配置错误=====
❌ 未配置青龙信息
------------------
请在插件配置中填写:
Host丨ClientID丨ClientSecret
• 使用中文丨分隔
• 示例:
http://ql.example.com丨abcd丨1234
==================""")
            exit(0)

        qllist = dd_sf_qlname.split('丨')
        if len(qllist) != 3:
            sender.reply("""
=====格式错误=====
❌ 青龙配置格式错误
------------------
当前格式: {dd_sf_qlname}
正确格式:
Host丨ClientID丨ClientSecret
==================""")
            exit(0)

        QLurl = qllist[0].strip()
        ClientID = qllist[1].strip()
        ClientSecret = qllist[2].strip()

        # 验证每个参数是否为空
        if not all([QLurl, ClientID, ClientSecret]):
            sender.reply("""
=====参数错误=====
❌ 青龙配置参数不完整
------------------
请确保以下参数都已填写:
• 青龙面板地址(Host)
• 应用ID(ClientID)
• 应用密钥(ClientSecret)
==================""")
            exit(0)

        # 验证URL格式
        if not QLurl.startswith(('http://', 'https://')):
            sender.reply(f"""
=====地址错误=====
❌ 青龙地址格式错误
------------------
当前地址: {QLurl}
正确格式:
• http://qinglong.example.com
• https://ql.example.com:5700
==================""")
            exit(0)

        try:
            qltoken = QLtoken(QLurl=QLurl, ClientID=ClientID, ClientSecret=ClientSecret)
            return QLurl, qltoken
        except Exception as e:
            raise Exception(f"获取Token失败: {str(e)}")

    except Exception as e:
        sender.reply(f"""
=====连接失败=====
❌ 无法连接青龙面板
------------------
请检查:
1. 青龙面板是否运行
2. 网络是否正常
3. 配置是否正确
4. 错误信息: {str(e)}
------------------
当前配置:
• 地址: {QLurl if 'QLurl' in locals() else '未设置'}
• 应用ID: {ClientID[:4] + '****' if 'ClientID' in locals() else '未设置'}
==================""")
        exit(0)


def delenvs(id):
    if id is None:
        return
    url = f"{QLurl}/open/envs"
    headers = {
        "Authorization": "Bearer" + ' ' + qltoken,
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    data = [id]
    response = requests.delete(url, headers=headers, json=data).json()


def allenvs(osname, account):
    url = f"{QLurl}/open/envs"
    headers = {
        "Authorization": "Bearer" + ' ' + qltoken,
        "accept": "application/json"
    }
    response = requests.get(url=url, headers=headers).json()
    qlid = None
    if response['code'] == 200:
        envslist = response['data']
        for envs in envslist:
            envname = envs['name']
            remarks = envs['remarks']
            if remarks is None:
                continue
            if osname == envname and str(account) in remarks:
                qlid = envs['id']
                break
        return qlid
    else:
        sender.reply('连接青龙获取变量失败')
        exit(0)


def Addenvs(osname, value, account, phone):
    phone = phone[:3] + '*' * 4 + phone[7:]
    url = f"{QLurl}/open/envs"
    headers = {
        "Authorization": "Bearer" + ' ' + qltoken,
        "accept": "application/json"
    }
    response = requests.get(url=url, headers=headers).json()
    qlid = None
    if response['code'] == 200:
        envslist = response['data']
        for envs in envslist:
            remarks = envs['remarks']
            envname = envs['name']
            if remarks is None:
                continue
            if account in remarks and osname == envname:
                qlid = envs['id']
                break
    else:
        sender.reply('连接青龙获取变量失败')
        exit(0)

    if qlid is None:
        QLzt(osname, value, account, phone)
    else:
        QLupdate(osname, value, account, qlid, phone)


def QLupdate(osname, value, account, qlid, phone):
    qlurl = f"{QLurl}/open/envs"
    # URL编码value
    value = urllib.parse.quote(value)
    data = {
        "value": value,
        "name": osname,
        "remarks": f'顺丰:{account}丨用户:{userid}丨手机:{phone}丨顺丰管理',
        "id": qlid
    }
    headers = {
        "Authorization": "Bearer" + ' ' + qltoken,
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    response = requests.put(qlurl, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        response_json = response.json()
        data = response_json['data']
        if data is None:
            exit(0)
        id = data['id']
        createdAt = data['createdAt']
        return id, createdAt
    else:
        sender.reply('更新变量失败,请联系管理员处理')
        exit(0)


def QLzt(osname, value, account, phone):  # 添加青龙变量
    try:
        qlurl = f"{QLurl}/open/envs"
        # URL编码value
        value = urllib.parse.quote(value)

        data = [{
            "value": value,
            "name": osname,
            "remarks": f'顺丰:{account}丨用户:{userid}丨手机:{phone}丨顺丰管理'
        }]

        headers = {
            "Authorization": f"Bearer {qltoken}",
            "accept": "application/json",
            "Content-Type": "application/json",
        }

        response = requests.post(qlurl, headers=headers, json=data)

        if response.status_code != 200:
            sender.reply(f"""
=====添加变量失败=====
❌ 请求失败
状态码: {response.status_code}
==================""")
            exit(0)

        result = response.json()
        if result.get('code') != 200:
            sender.reply(f"""
=====添加变量失败=====
❌ 青龙返回错误
错误信息: {result.get('message')}
==================""")
            exit(0)

        if "value must be unique" in response.text:
            # 变量已存在,不需要处理
            return

        data = result.get('data')
        if not data or not isinstance(data, list) or len(data) == 0:
            sender.reply("""
=====添加变量失败=====
❌ 青龙返回数据异常
==================""")
            exit(0)

        return data[0].get('id')

    except Exception as e:
        sender.reply(f"""
=====系统错误=====
❌ 添加青龙变量失败
------------------
错误信息: {str(e)}
==================""")
        exit(0)


def QLtoken(QLurl, ClientID, ClientSecret):  # 获取青龙token
    try:
        url = f'{QLurl}/open/auth/token?client_id={ClientID}&client_secret={ClientSecret}'
        response = requests.get(url)

        if response.status_code != 200:
            sender.reply(f"""
=====请求失败=====
❌ 青龙API请求失败
------------------
状态码: {response.status_code}
请检查:
• API地址是否正确
• 面板是否正常运行
==================""")
            exit(0)

        result = response.json()
        if "token" in result.get('data', {}):
            return result['data']['token']
        else:
            sender.reply("""
=====认证失败=====
❌ 获取Token失败
------------------
请检查:
• ClientID是否正确
• ClientSecret是否正确
• 应用是否有权限
==================""")
            exit(0)

    except requests.exceptions.RequestException as e:
        sender.reply(f"""
=====网络错误=====
❌ 连接青龙面板失败
------------------
请检查:
• 青龙地址是否正确
• 网络是否正常
• 错误信息: {str(e)}
==================""")
        exit(0)
    except Exception as e:
        sender.reply(f"""
=====系统错误=====
❌ 处理请求时出错
------------------
请检查:
• 配置格式是否正确
• 错误信息: {str(e)}
==================""")
        exit(0)


def session_ids(url):
    # 添加 URL 验证
    if not url:
        sender.reply('URL无效，请重新输入！')
        exit(0)

    # 验证 URL 格式
    if not url.startswith(('http://', 'https://')):
        sender.reply('URL格式错误，必须以 http:// 或 https:// 开头！')
        exit(0)

    try:
        response = requests.get(url, allow_redirects=False)
        session_id_pattern = r'sessionId=([^;]+);'
        login_mobile_pattern = r'_login_mobile_=([^;]+);'

        session_id_match = re.search(session_id_pattern, str(response.headers))
        login_mobile_match = re.search(login_mobile_pattern, str(response.headers))

        if not session_id_match or not login_mobile_match:
            sender.reply('无法从响应中获取用户信息，请检查URL是否正确！')
            exit(0)

        session_id = session_id_match.group(1)
        login_mobile = login_mobile_match.group(1)

        if '用户手机号校验未通过' in response.text:
            sender.reply('用户手机号校验未通过，请检查账号状态！')
            exit(0)

        return session_id, login_mobile

    except requests.exceptions.RequestException as e:
        sender.reply(f'网络请求失败: {str(e)}')
        exit(0)
    except Exception as e:
        sender.reply(f'处理用户信息时出错: {str(e)}')
        exit(0)


def Honey(session_id):
    url = "https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~indexData"

    headers = {
        "Cookie": f"sessionId={session_id}"
    }
    data = {}
    response = requests.post(url, headers=headers, json=data)
    honeydata = response.json()
    # success = honeydata['success']
    if '用户手机号校验未通过' not in response.text:
        capacity = honeydata['obj']['capacity']
        usableHoney = honeydata['obj']['usableHoney']
    else:
        capacity = '校验未通过'
        usableHoney = '0'
    return capacity, usableHoney


def todaycoin(session_id):
    pageNo = 1
    coin = 0
    while True:
        url = "https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberIntegral~memberPoint~queryMemberPointDetail"

        headers = {
            "Cookie": f"sessionId={session_id}"
        }

        data = {
            "type": "ALL",
            "pageNo": pageNo,
            "pageSize": 10
        }

        response = requests.post(url, headers=headers, json=data).json()
        success = response['success']
        data = response['obj']['data']
        if len(data) < 1:
            return 0, '0'
        if success:
            allcoin = response['obj']['usablePoint']
            for coinjson in data:
                createTm = coinjson['createTm']
                datetime_obj = datetime.strptime(createTm, "%Y-%m-%d %H:%M:%S")
                date_str = datetime_obj.strftime("%Y-%m-%d")
                if date_str < str(today_time):
                    break
                else:
                    opCode = coinjson['opCode']
                    pointVal = coinjson['pointVal']
                    if opCode == 'ADD':
                        coin = coin + int(pointVal)
                    else:
                        continue
            createTm = data[-1]['createTm']
            datetime_obj = datetime.strptime(createTm, "%Y-%m-%d %H:%M:%S")
            date_str = datetime_obj.strftime("%Y-%m-%d")
            if date_str >= str(today_time):
                pageNo = pageNo + 1
            else:
                break
    return coin, allcoin


def todayhoney(session_id):
    num = 2
    pageNo = 1
    honey = 0
    while True:
        url = "https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~detail"

        headers = {
            "Cookie": f"sessionId={session_id}"
        }

        data = {
            # "type": "ALL",
            "pageNo": pageNo,
            "pageSize": 10
        }

        response = requests.post(url, headers=headers, json=data).json()
        success = response['success']
        if success:
            allhoney = response['obj']['usableHoney']
            data = response['obj']['data']
            if len(data) == 0:
                break
            for coinjson in data:
                createTm = coinjson['time']
                datetime_obj = datetime.strptime(createTm, "%Y-%m-%d %H:%M:%S")
                date_str = datetime_obj.strftime("%Y-%m-%d")
                if date_str < str(today_time):
                    break
                else:
                    # opCode = coinjson['opCode']
                    pointVal = coinjson['value']
                    if '-' not in pointVal:
                        honey = honey + int(pointVal)
                    else:
                        continue
            createTm = data[-1]['time']
            datetime_obj = datetime.strptime(createTm, "%Y-%m-%d %H:%M:%S")
            date_str = datetime_obj.strftime("%Y-%m-%d")
            if date_str >= str(today_time):
                if len(data) < 10:
                    break
                else:
                    pageNo = pageNo + 1
            else:
                break
    return honey, allhoney


def ValueErrors(value, count):
    """验证输入值是否为有效的整数且在合理范围内"""
    try:
        value = int(value)
        if value > count or value == 0:
            sender.reply(f"""
=====输入无效=====
❌ 请输入 1-{count} 之间的数字
==================""")
            exit(0)
        return value
    except ValueError:
        sender.reply("""
=====输入无效=====
❌ 请输入正确的数字
==================""")
        exit(0)


def sytTokens(payload, deviceId):
    t = int(time.time() * 1000)
    datamd5 = generate_md5(payload + '&080R3MAC57J2{A19!$3:WO{I<1N$31BI')
    deviceidmd5 = generate_md5(
        deviceId + f'{t}' + '9.65.302NBF+BE4{@P:@X${Q9BAE>{PAK!D:N*^CNsc' + datamd5 + '705088894ad6ef475bdf4875c9d533b8&2NBF+BE4{@P:@X${Q9BAE>{PAK!D:N*^')

    sytToken = generate_md5(deviceidmd5 + '&0HQ%H91K&AA{DH$*XV>XR)VKL:QFE{&%')
    return sytToken, t


def generate_md5(input_string):
    md5_hash = hashlib.md5()
    md5_hash.update(input_string.encode('utf-8'))
    md5_digest = md5_hash.hexdigest()

    return md5_digest


def sf_login(sender):
    try:
        scan_msg = """
=====微信扫码登录=====
⌛ 正在加载二维码...
⏳ 请稍候...
=================="""
        mesid3 = sender.reply(scan_msg)

        url_getQr = '接口'
        url_checkQr = '接口'
        response = requests.post(url_getQr, json={'project': 'sf'})
        response_data = response.json()
        if not response_data.get('data') or 'uuid' not in response_data['data']:
            sender.reply('❌ 获取二维码失败!')
            exit(0)

        QRcode = response_data['data']['uuid']
        QRcodeImg = response_data['data']['img_url']

        mesid = sender.replyImage(QRcodeImg)

        scan_guide = """
=====登录说明=====
📱 请使用微信扫描二维码登录
------------------
⚠️ 注意事项:
1. 请确保已用微信登录过顺丰APP
2. 如果登录失败,请先下载顺丰APP
3. 使用微信登录APP后再次尝试
=================="""
        mesid2 = sender.reply(scan_guide)

        retry = 60
        while True:
            time.sleep(1)
            data = {'project': 'sf', 'uuid': QRcode}  # 使用 uuid 而不是 qrcode
            response = requests.post(url_checkQr, json=data)
            response_data = response.json()

            if response_data.get('code') == 0 and response_data.get('data', {}).get('code'):
                code = response_data['data']['code']
                break
            else:
                retry -= 1
                if retry == 0:
                    sender.reply('❌ 扫码超时,请重新尝试!')
                    exit(0)

        deviceId = str(uuid.uuid4())
        url = "https://ccsp-egmas.sf-express.com/cx-app-member/member/app/weixin/getAccessTokenByCode"
        payload = json.dumps({"code": code})
        sytToken, t = sytTokens(payload, deviceId)
        headers = {
            'User-Agent': "okhttp/4.9.1",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/json",
            'jsbundle': "705088894ad6ef475bdf4875c9d533b8",
            'clientVersion': "9.65.30",
            'languageCode': "sc",
            'systemVersion': "13",
            'deviceId': deviceId,
            'regionCode': "CN",
            'carrier': "unknown",
            'screenSize': "1080x2400",
            'sytToken': sytToken,
            'timeInterval': f"{t}",
            'model': "MEIZU 20",
            'mediaCode': "AndroidML"
        }
        response = requests.post(url, data=payload, headers=headers)
        url = "https://ccsp-egmas.sf-express.com/cx-app-member/member/app/user/universalSign"
        account = response.json()['obj']['memInfos'][0]['userId']
        memNo = response.json()['obj']['memInfos'][0]['memNo']
        mobile = response.json()['obj']['memInfos'][0]['mobile']

        payload = json.dumps({
            "mobile": mobile,
            "userId": account,
            "memNo": memNo,
            "name": "mcs-mimp-web.sf-express.com",
            "extra": "",
            "needReqTime": "1"
        })
        sytToken, t = sytTokens(payload, deviceId)
        headers['sytToken'] = sytToken
        headers['timeInterval'] = str(t)
        response = requests.post(url, data=payload, headers=headers)
        sign = response.json()['obj']['sign']
        encoded_string = urllib.parse.quote(sign)
        Token = f'https://mcs-mimp-web.sf-express.com/mcs-mimp/share/app/shareRedirect?sign={encoded_string}&source=SFAPP&bizCode=619'
        account = mobile
        mobile = mobile[:3] + '*' * 4 + mobile[7:]

        return Token, str(account), mobile
    except Exception as e:
        sender.reply(f'❌ 登录失败!，报错：{str(e)}')
        exit(0)


def bindaccount():
    welcome_msg = """
=====顺丰速运登录=====
[1] 微信扫码登录
[2] 手动链接登录
------------------
回复数字选择方式
回复"q"退出操作
=================="""

    sender.reply(welcome_msg)
    input_choice = sender.input(120000, 1, False)

    if input_choice == '1':
        Token, account, mobile = sf_login(sender)
    elif input_choice == '2':
        ck_guide = """
=====手动链接登录=====
请输入顺丰小程序抓包的完整URL
示例:https://mcs-mimp-web.sf-express.com/mcs-mimp/share/weChat/

✨ 抓包教程:
------------------
1. 打开抓包工具
2. 进入顺丰小程序
3. 找到上述域名开头的URL
4. 复制完整URL地址粘贴发送即可
=================="""
        sender.reply(ck_guide)

        while True:
            ck_input = sender.input(120000, 1, False)
            if not ck_input:
                sender.reply("⏰ 操作超时,已退出")
                exit(0)
            elif ck_input.lower() == 'q':
                sender.reply("✅ 已取消登录")
                exit(0)

            try:
                # 验证URL格式
                if not ck_input.startswith(('http://', 'https://')):
                    sender.reply("""
=====URL格式错误=====
❌ URL必须以http://或https://开头
请重新输入或回复"q"退出
==================""")
                    continue

                # 尝试获取session信息
                session_id, login_mobile = session_ids(ck_input)
                Token = ck_input
                account = login_mobile
                mobile = login_mobile[:3] + '*' * 4 + login_mobile[7:]
                break

            except Exception as e:
                sender.reply(f"""
=====验证失败提示=====
❌ URL验证失败
⚠️ 错误: {str(e)}
------------------
请检查URL是否正确
重新输入或回复"q"退出
==================""")
                continue
    else:
        sender.reply('❌ 输入错误,请重新选择登录方式')
        return

    # 处理账号绑定逻辑
    def accvip(account, Token, mobile):
        accountVip = middleware.bucketGet(bucket='dd_sf_auth', key=account)
        auth_status = '✅ 已授权' if accountVip and accountVip >= today_time else '⚠️ 未授权'
        next_step = f'发送 {randommanagecommand} 可管理账号' if accountVip and accountVip >= today_time else f'发送 {randommanagecommand} 可进行授权'

        success_msg = f"""
=====顺丰账号绑定=====
📱 绑定账号: {mobile}
🔐 授权状态: {auth_status}
⏰ 下一步操作: 
   {next_step}
=================="""

        # 获取并处理账号列表
        accounts = []
        if uservalue:
            try:
                existing_accounts = eval(uservalue)
                if isinstance(existing_accounts, (list, tuple, set)):
                    accounts = list(existing_accounts)
                else:
                    accounts = [str(existing_accounts)]
            except:
                accounts = []

        # 确保账号不重复
        if account not in accounts:
            accounts.append(account)

        # 使用集合去重并保持顺序
        accounts = list(dict.fromkeys(accounts))

        # 更新用户账号列表
        if accounts:
            middleware.bucketSet(bucket='dd_sf_user', key=userid, value=str(accounts))

        # 更新token
        middleware.bucketSet(bucket='dd_sf_token', key=account, value=Token)

        # 只有在已授权的情况下才更新青龙变量
        if accountVip and accountVip >= today_time:
            try:
                qlid = allenvs(osname=dd_sf_osname, account=account)
                if qlid:
                    # 如果变量存在，更新它
                    QLupdate(osname=dd_sf_osname, value=Token, account=account, qlid=qlid, phone=mobile)
                else:
                    # 如果变量不存在，添加新的
                    Addenvs(osname=dd_sf_osname, value=Token, account=account, phone=mobile)
            except Exception as e:
                sender.reply(f"""
=====青龙更新失败=====
❌ 更新青龙变量失败
⚠️ 错误: {str(e)}
==================""")

        sender.reply(success_msg)

    # 调用修改后的accvip函数
    accvip(account, Token, mobile)


def empower(empowertime, me_as_int):
    """授权时间计算"""
    day = me_as_int * 30
    if len(empowertime) == 0 or empowertime <= str(today_time):
        delayed_date = today_date + timedelta(days=day)
    elif empowertime > today_time:
        empower_date = datetime.strptime(empowertime, "%Y-%m-%d")
        delayed_date = empower_date + timedelta(days=day)
        delayed_date = delayed_date.date()
    else:
        sender.reply('出错！')
        exit(0)
    return str(delayed_date)


def sf_auth():
    """顺丰授权功能"""
    if not sender.isAdmin():
        sender.reply("❌ 您没有权限执行此操作!")
        exit(0)

    auth_menu = """
=====顺丰授权管理=====
[1] 一键授权所有用户
[2] 单独授权用户
------------------
回复数字选择功能
回复"q"退出
=================="""
    sender.reply(auth_menu)
    xz = sender.listen(60000)

    if xz == 'q' or xz == 'Q':
        sender.reply("✅ 已退出授权管理")
        return
    elif xz is None:
        sender.reply("⏰ 操作超时,已退出")
        return
    elif xz == '1':
        # 一键授权所有用户
        users = middleware.bucketAllKeys('dd_sf_user')
        if not users:
            sender.reply("❌ 未找到任何绑定的顺丰账号")
            return

        sender.reply("""
=====请输入授权天数=====
------------------
回复数字设置天数
回复"q"退出操作
==================""")

        sjts = sender.listen(60000)
        if sjts == 'q' or sjts == 'Q':
            sender.reply("✅ 已取消授权")
            return
        elif sjts is None:
            sender.reply("⏰ 操作超时,已退出")
            return

        try:
            sjts = int(sjts)  # 确保转换为整数
        except:
            sender.reply("❌ 天数必须是数字!")
            return

        success_count = 0
        fail_count = 0

        for user in users:
            accountlist = middleware.bucketGet('dd_sf_user', user)
            if accountlist == '' or accountlist == '{}':
                continue

            accounts = eval(accountlist)
            for account in accounts:
                try:
                    dqsj = datetime.now().strftime("%Y-%m-%d")
                    accountVip = middleware.bucketGet('dd_sf_auth', account)
                    token = middleware.bucketGet('dd_sf_token', account)

                    if not token:
                        fail_count += 1
                        continue

                    if len(accountVip) != 0 and accountVip > dqsj:
                        sqsj = datetime.strptime(accountVip, "%Y-%m-%d")
                        new_sqsj = sqsj + timedelta(days=int(sjts))  # 确保使用整数
                    else:
                        new_sqsj = datetime.now() + timedelta(days=int(sjts))  # 确保使用整数
                    new_sqsj = new_sqsj.strftime("%Y-%m-%d")

                    # 更新授权时间
                    middleware.bucketSet('dd_sf_auth', account, new_sqsj)

                    # 更新青龙变量
                    phone = account[:3] + '*' * 4 + account[7:]
                    Addenvs(osname=dd_sf_osname, value=token, account=account, phone=phone)
                    success_count += 1
                except:
                    fail_count += 1

        result_msg = f"""
=====授权操作完成=====
✅ 成功: {success_count} 个账号
❌ 失败: {fail_count} 个账号
⏰ 授权: {sjts} 天
=================="""
        sender.reply(result_msg)

        # 发送管理员通知
        notify = middleware.bucketGet('bd_tptconfig', 'notify')
        if notify:
            tsqd = notify.split(',')
            middleware.notifyMasters(result_msg, tsqd)

    elif xz == '2':
        # 单独授权用户
        user_guide = """
======账号授权======
请输入需要授权的账号ID
(发送myuid可获取ID)
------------------
回复"q"退出操作
=================="""
        sender.reply(user_guide)

        myuid = sender.listen(60000)
        if myuid == 'q' or myuid == 'Q':
            sender.reply("✅ 已退出授权")
            return
        elif myuid is None:
            sender.reply("⏰ 操作超时,已退出")
            return

        accountlist = middleware.bucketGet('dd_sf_user', myuid)
        if accountlist == '' or accountlist == '{}':
            sender.reply(f"❌ 未找到 {myuid} 的顺丰账号信息!")
            return

        accounts = eval(accountlist)
        account_list = """
=======账号列表=====
[0] 授权所有账号
------------------"""

        for i, account in enumerate(accounts, 1):
            accountVip = middleware.bucketGet('dd_sf_auth', account)
            vip_status = accountVip if accountVip else '未授权'
            account_list += f"\n[{i}] 账号: {account}\n    授权至: {vip_status}\n------------------"

        account_list += "\n回复数字选择账号\n回复'q'退出\n=================="
        sender.reply(account_list)

        xz = sender.listen(60000)
        if xz == 'q' or xz == 'Q':
            sender.reply("✅ 已退出授权")
            return
        elif xz is None:
            sender.reply("⏰ 操作超时,已退出")
            return

        auth_guide = """
=====设置授权天数=====
请输入要授权的天数
------------------
回复数字设置天数
回复"q"退出操作
=================="""

        if xz == '0':
            # 授权该用户的所有账号
            sender.reply(auth_guide)
            sjts = sender.listen(60000)
            if sjts == 'q' or sjts == 'Q':
                sender.reply("✅ 已取消授权")
                return
            elif sjts is None:
                sender.reply("⏰ 操作超时,已退出")
                return

            try:
                sjts = int(sjts)  # 确保转换为整数
                success_count = 0
                for account in accounts:
                    try:
                        dqsj = datetime.now().strftime("%Y-%m-%d")
                        accountVip = middleware.bucketGet('dd_sf_auth', account)
                        token = middleware.bucketGet('dd_sf_token', account)

                        if not token:
                            continue

                        if len(accountVip) != 0 and accountVip > dqsj:
                            sqsj = datetime.strptime(accountVip, "%Y-%m-%d")
                            new_sqsj = sqsj + timedelta(days=int(sjts))
                        else:
                            new_sqsj = datetime.now() + timedelta(days=int(sjts))
                        new_sqsj = new_sqsj.strftime("%Y-%m-%d")

                        # 更新授权时间
                        middleware.bucketSet('dd_sf_auth', account, new_sqsj)

                        # 更新青龙变量
                        phone = account[:3] + '*' * 4 + account[7:]
                        Addenvs(osname=dd_sf_osname, value=token, account=account, phone=phone)
                        success_count += 1
                    except:
                        continue

                result_msg = f"""
=====授权操作完成=====
📱 账号: {account}
⏰ 授权天数: {sjts} 天
📅 到期时间: {new_sqsj}
=================="""
                sender.reply(result_msg)

            except ValueError:
                sender.reply("❌ 天数必须是数字!")
                return

        elif 1 <= int(xz) <= len(accounts):
            # 授权单个账号
            account = accounts[int(xz) - 1]
            sender.reply(auth_guide)
            sjts = sender.listen(60000)

            if sjts == 'q' or sjts == 'Q':
                sender.reply("✅ 已取消授权")
                return
            elif sjts is None:
                sender.reply("⏰ 操作超时,已退出")
                return

            try:
                sjts = int(sjts)  # 确保转换为整数
                dqsj = datetime.now().strftime("%Y-%m-%d")
                accountVip = middleware.bucketGet('dd_sf_auth', account)
                token = middleware.bucketGet('dd_sf_token', account)

                if not token:
                    sender.reply("未找到账号token信息!")
                    return

                if len(accountVip) != 0 and accountVip > dqsj:
                    sqsj = datetime.strptime(accountVip, "%Y-%m-%d")
                    new_sqsj = sqsj + timedelta(days=int(sjts))
                else:
                    new_sqsj = datetime.now() + timedelta(days=int(sjts))
                new_sqsj = new_sqsj.strftime("%Y-%m-%d")

                # 更新授权时间
                middleware.bucketSet('dd_sf_auth', account, new_sqsj)

                # 更新青龙变量
                phone = account[:3] + '*' * 4 + account[7:]
                Addenvs(osname=dd_sf_osname, value=token, account=account, phone=phone)

                msg = f"""
=====授权成功=====
📱 账号: {account}
⏰ 授权天数: {sjts}天
📅 到期时间: {new_sqsj}
=================="""
                sender.reply(msg)

            except ValueError:
                sender.reply('❌ 输入的天数无效!')
                return
        else:
            sender.reply("❌ 输入的序号无效!")
            return


def meituanmanage():
    if len(uservalue) != 0:
        count = 1
        account_list = """
======我的顺丰账号====="""
        try:
            # 解析并去重账号列表
            accounts = eval(uservalue)
            if isinstance(accounts, (list, tuple, set)):
                # 使用字典键去重并保持顺序
                accounts = list(dict.fromkeys(accounts))
            else:
                accounts = [str(accounts)]

            # 更新存储的账号列表(去重后)
            middleware.bucketSet(bucket='dd_sf_user', key=userid, value=str(accounts))

            for account in accounts:
                accountVip = middleware.bucketGet(bucket='dd_sf_auth', key=f'{account}')
                if len(accountVip) == 0:
                    vip_status = '⚠️ 未授权'
                elif accountVip < today_time:
                    vip_status = '❌ 已过期'
                else:
                    vip_status = f'✅ {accountVip}'

                # 这里直接使用 account 作为手机号显示
                login_mobile = account[:3] + "****" + account[7:]
                account_list += f"""
------------------
[{count}] 账号信息
📱 账号: {login_mobile}
🔐 授权: {vip_status}"""
                count += 1

            account_list += """
=====回复数字选择账号=====
回复"q"退出操作
=================="""

            sender.reply(account_list)

            # 修改这里的输入处理
            inputmessage = sender.input(120000, 1, False)
            if inputmessage is None or inputmessage == 'timeout':
                sender.reply('⏰ 操作超时,已退出')
                exit(0)
            elif inputmessage == 'q' or inputmessage == 'Q':
                sender.reply('✅ 已退出管理')
                exit(0)

            try:
                me_as_int = int(inputmessage)
                if me_as_int <= 0 or me_as_int >= count:
                    sender.reply('❌ 输入的序号无效')
                    exit(0)
            except ValueError:
                sender.reply('❌ 输入必须是数字')
                exit(0)
            except TypeError:
                sender.reply('⏰ 操作超时,已退出')
                exit(0)

            account = accounts[me_as_int - 1]
            userurl = middleware.bucketGet(bucket='dd_sf_token', key=f'{account}')
            accountVip = middleware.bucketGet(bucket='dd_sf_auth', key=f'{account}')
            session_id, login_mobile = session_ids(userurl)

            if len(accountVip) == 0:
                vip_status = '⚠️ 未授权'
            elif accountVip < today_time:
                vip_status = '❌ 已过期'
            else:
                vip_status = f'✅ {accountVip}'

            login_mobile = login_mobile[:3] + "****" + login_mobile[7:]

            account_info = f"""
=====账号详情=====
📱 账号: {login_mobile}
🔐 授权: {vip_status}
=================="""
            sender.reply(account_info)

            menu = """
=====账号管理=====
[1] 授权账号
[2] 删除账号
------------------
回复数字选择功能
回复"q"退出操作
=================="""
            sender.reply(menu)

            inputmessage = sender.input(120000, 1, False)
            if inputmessage is None or inputmessage == 'timeout':
                sender.reply('⏰ 操作超时,已退出')
                exit(0)
            elif inputmessage == 'q' or inputmessage == 'Q':
                sender.reply('✅ 已退出管理')
                exit(0)
            elif inputmessage == '2':
                confirm_msg = """
=====警告=====
确定要删除该账号吗？
此操作不可恢复！
------------------
[y] 确认删除
[n] 取消操作
=================="""
                sender.reply(confirm_msg)

                yesorno = sender.input(120000, 1, False)
                if yesorno is None or yesorno == 'timeout':
                    sender.reply('⏰ 操作超时,已退出')
                    exit(0)
                elif yesorno == 'Y' or yesorno == 'y' or yesorno == '是':
                    accounts.remove(str(account))
                    qlid = allenvs(osname=dd_sf_osname, account=str(account))
                    delenvs(id=qlid)
                    if len(accounts) == 0:
                        middleware.bucketDel(bucket='dd_sf_user', key=userid)
                    else:
                        middleware.bucketSet(bucket='dd_sf_user', key=userid, value=f'{accounts}')
                    sender.reply('✅ 账号删除成功!')
                elif yesorno == 'n' or yesorno == 'N' or yesorno == '否':
                    sender.reply('✅ 已取消删除')
                    exit(0)
            elif inputmessage == '1':
                auth_guide = """
=====设置授权时长=====
请输入授权月数(如:1)
------------------
回复数字设置月数
回复"q"退出操作
=================="""
                sender.reply(auth_guide)

                mes = sender.input(120000, 1, False)
                if mes is None or mes == 'timeout':
                    sender.reply('⏰ 操作超时,已退出')
                    exit(0)
                elif mes == 'q' or mes == 'Q':
                    sender.reply('✅ 已退出管理')
                    exit(0)
                mes = ValueErrors(value=mes, count=999)
                money = Decimal(mes) * Decimal(sfVipmoney)
                zf(project='顺丰授权', me_as_int=mes, accountVip=accountVip, token=userurl,
                   phone=account, account=account)
                accountVip = empower(empowertime=accountVip, me_as_int=mes)
                Addenvs(osname=dd_sf_osname, value=f'{userurl}', account=account, phone=login_mobile)
                middleware.bucketSet(bucket='dd_sf_auth', key=f'{account}', value=f'{accountVip}')

                result_msg = f"""
=====订单完成=====
🎈 名称: 顺丰授权
🎉 数量: {mes} 个月
💰 金额: {money} 元
=================="""
                sender.reply(result_msg)

            elif inputmessage == 'q' or inputmessage == 'Q':
                sender.reply('✅ 已退出管理')
        except Exception as e:
            sender.reply(f"""
=====账号处理错误=====
❌ 账号列表处理失败
⚠️ 错误: {str(e)}
==================""")
            return
    else:
        sender.reply(f"""
=====未绑定账号=====
❌ 未找到任何账号信息
💡 发送 {randomsigncommand} 绑定
==================""")


def yesornos():
    yesorno = sender.input(120000, 1, False)
    if yesorno == 'Y' or yesorno == 'y' or yesorno == '是':
        return True
    elif yesorno == 'n' or yesorno == 'N' or yesorno == '否':
        return False
    elif yesorno == '':
        sender.reply('输入超时！')
        exit(0)
    elif yesorno == 'q' or yesorno == 'Q' or yesorno == '退出':
        sender.reply('退出!')
        exit(0)
    else:
        sender.reply('输入错误！')
        exit(0)


def zf(project, me_as_int, accountVip, token, phone, account):
    """处理支付流程"""
    try:
        # 获取支付配置
        zsm = middleware.bucketGet('dd_sf', 'zsm')
        use_ma_pay = middleware.bucketGet('dd_sf', 'use_ma_pay') or 'false'
        use_ma_pay = use_ma_pay.lower() == 'true'

        if use_ma_pay:
            # 从卡密系统获取码支付配置
            ma_pay_config = {
                'switch': middleware.bucketGet('dd_sign_config', 'ma_pay_switch') or 'false',
                'gateway': middleware.bucketGet('dd_sign_config', 'ma_pay_gateway'),
                'pid': middleware.bucketGet('dd_sign_config', 'ma_pay_pid'),
                'key': middleware.bucketGet('dd_sign_config', 'ma_pay_key'),
                'type': middleware.bucketGet('dd_sign_config', 'ma_pay_type'),
                'notify_url': middleware.bucketGet('dd_sign_config', 'ma_pay_notify_url'),
                'return_url': middleware.bucketGet('dd_sign_config', 'ma_pay_return_url')
            }

            if ma_pay_config['switch'].lower() != 'true' or not all(
                    [ma_pay_config['gateway'], ma_pay_config['pid'], ma_pay_config['key']]):
                use_ma_pay = False

        if not zsm and not use_ma_pay:
            sender.reply('未配置收款方式,请联系管理员!')
            exit(0)

        # 检查是否允许使用积分支付
        usercoin = middleware.bucketGet('dd_sign_points', userid) or '0'
        zfcoin = int(sfcoin) * me_as_int

        # 构建支付选择菜单
        pay_menu = """
=====选择支付方式===="""

        # 添加微信支付选项
        if zsm:
            money = Decimal(me_as_int) * Decimal(sfVipmoney)
            pay_menu += f"""
1️⃣ 微信支付
   💰 {money}元/{me_as_int}月"""

        # 添加码支付选项
        if use_ma_pay:
            money = Decimal(me_as_int) * Decimal(sfVipmoney)
            pay_menu += f"""
2️⃣ 码支付
   💰 {money}元/{me_as_int}月"""

        # 只有当sfcoin > 0时才显示积分支付选项
        if sfcoin and int(sfcoin) > 0:
            pay_menu += f"""
3️⃣ 积分支付  
   🎯 {zfcoin}积分/{me_as_int}月
   💫 当前积分: {usercoin}"""

        pay_menu += """
------------------
回复数字选择方式
回复"q"退出操作
=================="""

        sender.reply(pay_menu)
        choice = sender.input(60000, 1, False)

        if choice == 'q' or choice == 'Q':
            sender.reply("✅ 已取消支付")
            exit(0)

        elif choice == '1' and zsm:
            # 微信支付流程
            zfzt = sender.atWaitPay()
            if zfzt:
                sender.reply('⚠️ 当前有人正在支付,请稍后再试！')
                exit(0)

            money = Decimal(me_as_int) * Decimal(sfVipmoney)

            pay_msg = f"""
=====微信扫码支付====
🎫 商品: {project}
📅 时长: {me_as_int}月
💰 金额: {money}元
------------------
请使用微信扫码支付
回复"q"取消支付
=================="""
            sender.reply(pay_msg)
            sender.replyImage(zsm)

            ddzf = sender.waitPay("q", 100 * 1000)

            if str(ddzf) == 'q':
                sender.reply('✅ 已取消支付')
                exit(0)

            try:
                if isinstance(ddzf, dict):
                    # 新版微信赞赏消息格式
                    if ddzf.get('Type') == '微信赞赏':
                        Money = float(ddzf.get('Money', 0))
                        Time = ddzf.get('Time', '').split('.')[0].replace('T', ' ')
                        From = ddzf.get('FromName', '')
                    # 新版微信收款消息格式
                    elif ddzf.get('Type') == '微信收款':
                        Money = float(ddzf.get('Money', 0))
                        Time = ddzf.get('Time', '').split('.')[0].replace('T', ' ')
                        From = ddzf.get('FromName', '')
                    # 旧版BORW格式
                    elif ddzf.get('Money'):
                        Money = float(ddzf.get('Money', 0))
                        Time = ddzf.get('Time', '').replace('T', ' ').split('.')[0]
                        From = ddzf.get('FromName', '')
                    # 旧版GW格式
                    elif ddzf.get('money'):
                        Money = float(ddzf.get('money', 0))
                        Time = ddzf.get('time', '').replace('T', ' ').split('.')[0]
                        From = ddzf.get('fromName', '')
                    else:
                        sender.reply('不支持的支付消息格式')
                        exit(0)
                else:
                    # 尝试解析JSON字符串
                    try:
                        ddzf = json.loads(ddzf)
                        if ddzf.get('Type') == '微信赞赏':
                            Money = float(ddzf.get('Money', 0))
                            Time = ddzf.get('Time', '').split('.')[0].replace('T', ' ')
                            From = ddzf.get('FromName', '')
                        elif ddzf.get('Type') == '微信收款':
                            Money = float(ddzf.get('Money', 0))
                            Time = ddzf.get('Time', '').split('.')[0].replace('T', ' ')
                            From = ddzf.get('FromName', '')
                        else:
                            Money = float(ddzf.get('Money', 0))
                            Time = ddzf.get('Time', '').replace('T', ' ').split('.')[0]
                            From = ddzf.get('FromName', '')
                    except:
                        sender.reply("❌ 无法解析支付结果")
                        exit(0)

                if float(Money) >= float(money):
                    accountVip = empower(empowertime=accountVip, me_as_int=me_as_int)
                    middleware.bucketSet('dd_sf_auth', account, accountVip)
                    Addenvs(osname=dd_sf_osname, value=token, account=account, phone=phone)

                    result_msg = f"""
=====支付成功=====
🎫 商品: {project}
💰 金额: {Money}元
⏰ 时间: {Time}
{f'👤 付款人: {From}' if From else ''}
=================="""
                    sender.reply(result_msg)
                    return True
                else:
                    sender.reply(f"""
=====支付金额错误=====
💰 应付: {money}元
💳 实付: {Money}元
{f'👤 付款人: {From}' if From else ''}

❗ 请联系管理员处理退款！
==================""")
                    exit(0)
            except Exception as e:
                sender.reply(f"❌ 处理支付结果时出错: {str(e)}")
                exit(0)

        elif choice == '2' and use_ma_pay:
            # 码支付流程
            money = Decimal(me_as_int) * Decimal(sfVipmoney)

            # 生成订单号
            out_trade_no = f"SF{int(time.time())}{userid}"

            # 构造支付参数
            params = {
                'pid': ma_pay_config['pid'],
                'type': ma_pay_config['type'].split(',')[0],  # 默认使用第一个支付方式
                'out_trade_no': out_trade_no,
                'name': f"{senderID}-顺丰授权-{str(money)}",
                'money': str(money),
                'notify_url': ma_pay_config['notify_url'],
                'return_url': ma_pay_config['return_url'],
                'param': userid  # 传递用户ID作为附加参数
            }

            # 按照ASCII码排序参数
            sorted_params = sorted(params.items(), key=lambda x: x[0])

            # 拼接成URL键值对格式
            sign_str = "&".join([f"{k}={v}" for k, v in sorted_params])

            # 添加密钥进行MD5签名
            sign = hashlib.md5((sign_str + ma_pay_config['key']).encode()).hexdigest().lower()

            # 添加签名到参数
            params['sign'] = sign
            params['sign_type'] = 'MD5'

            # 发送支付请求
            gateway = ma_pay_config['gateway']
            if not gateway.endswith('/'):
                gateway += '/'
            submit_url = gateway + 'submit.php'

            try:
                response = requests.post(submit_url, data=params)
                if 'location.href' in response.text:
                    # 提取支付URL
                    match = re.search(r'location\.href\s*=\s*[\'"](.*?)[\'"]', response.text)
                    if match:
                        pay_url = match.group(1)
                        if not pay_url.startswith('http'):
                            pay_url = gateway + pay_url

                        sender.reply(f"""
=====码支付=====
🎫 商品: {project}
💰 金额: {money}元
⏰ 有效期: 5分钟
------------------
请点击链接完成支付:
{pay_url}
==================""")

                        # 轮询订单状态
                        for _ in range(60):  # 最多等待5分钟
                            time.sleep(5)
                            check_url = gateway + 'api.php'
                            check_params = {
                                'act': 'order',
                                'pid': ma_pay_config['pid'],
                                'key': ma_pay_config['key'],
                                'out_trade_no': out_trade_no
                            }

                            try:
                                check_resp = requests.get(check_url, params=check_params)
                                result = check_resp.json()

                                if result.get('code') == 1:  # 支付成功
                                    accountVip = empower(empowertime=accountVip, me_as_int=me_as_int)
                                    middleware.bucketSet('dd_sf_auth', account, accountVip)
                                    Addenvs(osname=dd_sf_osname, value=token, account=account, phone=phone)

                                    sender.reply(f"""
=====支付成功=====
🎫 商品: {project}
💰 金额: {money}元
⏰ 授权时长: {me_as_int}月
==================""")
                                    return True
                            except:
                                continue

                        sender.reply("❌ 支付超时,请重新发起支付!")
                        exit(0)
                else:
                    sender.reply("❌ 创建支付订单失败!")
                    exit(0)
            except Exception as e:
                sender.reply(f"❌ 支付请求失败: {str(e)}")
                exit(0)

        elif choice == '3' and sfcoin != 9999:
            # 积分支付流程
            if int(usercoin) < zfcoin:
                sender.reply(f"""
==================
    积分不足
==================
👤 当前积分: {usercoin}
📍 需要积分: {zfcoin}
==================""")
                exit(0)

            confirm_msg = f"""
==================
    积分支付确认
==================
💫 消耗积分: {zfcoin}
⏰ 授权时长: {me_as_int}月
------------------
确认请回复【y】
取消请回复【n】
=================="""
            sender.reply(confirm_msg)

            if yesornos():
                try:
                    new_balance = int(usercoin) - zfcoin
                    middleware.bucketSet('dd_sign_points', userid, str(new_balance))
                    accountVip = empower(empowertime=accountVip, me_as_int=me_as_int)
                    middleware.bucketSet('dd_sf_auth', account, accountVip)
                    Addenvs(osname=dd_sf_osname, value=token, account=account, phone=phone)

                    result_msg = f"""
==================
    支付成功
==================
💫 扣除积分: {zfcoin}
💰 剩余积分: {new_balance}
⏰ 授权时长: {me_as_int}月
=================="""
                    sender.reply(result_msg)
                    exit(0)
                except Exception as e:
                    sender.reply(f"""
==================
    支付失败
==================
❌ 积分处理失败
------------------
错误信息: {str(e)}
==================""")
                    exit(0)
            else:
                sender.reply("""
==================
    已取消支付
==================
✅ 操作已取消
==================""")
                exit(0)
        else:
            sender.reply("""
==================
    输入无效
==================
❌ 请输入正确的选项
==================""")
            exit(0)

    except Exception as e:
        sender.reply(f"""
==================
    系统错误
==================
❌ 支付处理异常
------------------
错误信息: {str(e)}
==================""")
        exit(0)


def cx(url):
    session_id, login_mobile = session_ids(url)
    coin, allcoin = todaycoin(session_id)
    honey, allhoney = todayhoney(session_id)
    capacity, usableHoney = Honey(session_id)
    wealth_status = YEAEND_2024_wealthStatus(session_id)
    large_coupons = query_large_coupons(session_id)
    if capacity == '查询失败':
        exit(0)
    return coin, allcoin, honey, allhoney, capacity, usableHoney, wealth_status, large_coupons


def cxs():
    if len(uservalue) != 0:
        # 使用字典来保持顺序的同时去重
        accounts = list(dict.fromkeys(eval(uservalue)))

        # 更新存储的账号列表(去重但保持原有顺序)
        middleware.bucketSet(bucket='dd_sf_user', key=userid, value=str(accounts))

        # 获取当前季度结束日期
        current_date = datetime.now()
        current_month = current_date.month
        current_year = current_date.year
        next_quarter_first_day = datetime(current_year, ((current_month - 1) // 3 + 1) * 3 + 1, 1)
        quarter_end_date = next_quarter_first_day - timedelta(days=1)
        days_left = (quarter_end_date - current_date).days

        # 只在最后一天显示单独提醒
        if days_left == 0:
            sender.reply("""
=====采蜜活动提醒=====
⚠️ 今天是采蜜活动最后兑换日
❗ 请务必及时兑换
==================""")

        for account in accounts:
            userurl = middleware.bucketGet(bucket='dd_sf_token', key=f'{account}')
            accountVip = middleware.bucketGet(bucket='dd_sf_auth', key=f'{account}')
            login_mobile = account[:3] + "****" + account[7:]

            # 处理授权状态显示
            if len(accountVip) == 0:
                auth_status = "⚠️ 未授权"
                auth_time = "无"
            elif accountVip <= today_time:
                auth_status = "❌ 已过期"
                auth_time = accountVip
            else:
                auth_status = "✅ 已授权"
                auth_time = accountVip

            if len(accountVip) != 0 and accountVip > today_time:
                try:
                    coin, allcoin, honey, allhoney, capacity, usableHoney, wealth_status, large_coupons = cx(userurl)
                    wealth_info = ""
                    if wealth_status:
                        wealth_info = f"""
------------------
🏅 勋章卡片收集：
🍚 干饭圣体: {wealth_status.get('干饭圣体', 0)}张
💧 心如止水: {wealth_status.get('心如止水', 0)}张  
🛡️ 都顶得住: {wealth_status.get('都顶得住', 0)}张
💰 坐以待币: {wealth_status.get('坐以待币', 0)}张
🏆 成功人士: {wealth_status.get('成功人士', 0)}张
❤️ 贴贴卡: {wealth_status.get('贴贴卡', 0)}张"""

                    # 根据配置决定是否显示积分状态
                    point_status_info = ""
                    if show_point_status:
                        point_status_info = f"\n📊 积分状态: {'❌ 积分黑号' if int(coin) == 0 else '✅ 积分正常'}"

                    account_info = f"""
=====账号详情=====
📱 账号: {login_mobile}
🔐 授权状态: {auth_status}
📅 到期时间: {auth_time}
------------------
💎 当前积分: {allcoin}
📈 今日积分: {coin}{point_status_info}
------------------
🔥 当前蜂蜜: {allhoney}
📊 今日蜂蜜: {honey}
🏺 蜜罐容量: {capacity}
⏰ 采蜜兑换: 剩余{days_left}天  
------------------
🎫 大额优惠券:
{large_coupons}
"""
                    sender.reply(account_info)

                except SystemExit:
                    sender.reply(f"""
=====顺丰查询异常=====
📱 账号: {login_mobile}
🔐 授权状态: {auth_status}
📅 到期时间: {auth_time}
❌ 状态: 查询失败
==================""")
                    continue
            else:
                sender.reply(f"""
=====顺丰授权过期=====
📱 账号: {login_mobile}
🔐 授权状态: {auth_status}
📅 到期时间: {auth_time}
==================""")
    else:
        sender.reply(f"""
=====未绑定账号=====
❌ 未找到任何账号信息
💡 发送 {randomsigncommand} 绑定
==================""")


def push(user, account, c):
    login_mobile = account[:3] + "****" + account[7:]

    push_msg = f"""
=====顺丰账号通知=====
📱 账号: {login_mobile}
📢 消息: {c}
=================="""

    # 发送到各个平台
    middleware.push('wb', '', user, '', push_msg)
    middleware.push('tg', '', user, '', push_msg)
    middleware.push('qq', '', user, '', push_msg)
    middleware.push('qb', '', user, '', push_msg)
    middleware.push('wx', '', user, '', push_msg)


def YEAEND_2024_wealthStatus(session_id):
    """查询勋章卡片状态"""
    url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2025ClaimService~claimStatus'
    headers = {
        "Cookie": f"sessionId={session_id}"
    }

    try:
        response = requests.post(url, headers=headers, json={})
        if response.json().get('success'):
            obj = response.json().get('obj')
            if not obj:
                return None

            currentAccountList = obj.get('currentAccountList', [])
            card_counts = {
                'GAN_FAN': 0,  # 干饭圣体
                'ZHI_SHUI': 0,  # 心如止水
                'DING_ZHU': 0,  # 都顶得住
                'DAI_BI': 0,  # 坐以待币
                'CHENG_GONG': 0,  # 成功人士
                'TIETIE_CARD': 0,  # 贴贴卡
            }

            # 用于显示的中文名称映射
            card_names = {
                'GAN_FAN': '干饭圣体',
                'ZHI_SHUI': '心如止水',
                'DING_ZHU': '都顶得住',
                'DAI_BI': '坐以待币',
                'CHENG_GONG': '成功人士',
                'TIETIE_CARD': '贴贴卡',
            }

            for item in currentAccountList:
                currency = item.get('currency')
                balance = item.get('balance', 0)
                if currency in card_counts:
                    card_counts[currency] = balance

            # 转换为显示友好的格式
            display_counts = {}
            for code, count in card_counts.items():
                if code in card_names:
                    display_counts[card_names[code]] = count

            return display_counts

    except Exception as e:
        sender.reply(f"""
=====查询异常=====
❌ 获取勋章卡片信息失败
⚠️ 错误: {str(e)}
==================""")

    return None


def clean_expired_accounts():
    """清理过期的顺丰账号"""
    if not sender.isAdmin():
        sender.reply("""
=====权限不足=====
❌ 您没有权限执行此操作
==================""")
        exit(0)

    users = middleware.bucketAllKeys(bucket='dd_sf_user')

    if not users:
        sender.reply("""
=====清理结果=====
❌ 未找到任何绑定账号
==================""")
        exit(0)

    sender.reply(f"""
=====开始清理=====
📊 共找到: {len(users)}个用户
⏳ 清理中请稍候...
==================""")

    cleaned_count = 0
    for user in users:
        try:
            accountlist = middleware.bucketGet(bucket='dd_sf_user', key=f'{user}')
            if not accountlist:
                continue

            # 解析并去重账号列表
            accounts = eval(accountlist)
            if isinstance(accounts, (list, tuple, set)):
                accounts = list(dict.fromkeys(accounts))
            else:
                accounts = [str(accounts)]

            valid_accounts = []

            for account in accounts:
                accountVip = middleware.bucketGet(bucket='dd_sf_auth', key=account)

                if len(accountVip) == 0 or accountVip <= today_time:
                    try:
                        qlid = allenvs(osname=dd_sf_osname, account=account)
                        if qlid:
                            delenvs(id=qlid)
                    except:
                        pass

                    middleware.bucketDel(bucket='dd_sf_token', key=account)
                    middleware.bucketDel(bucket='dd_sf_auth', key=account)
                    cleaned_count += 1
                else:
                    valid_accounts.append(account)

            # 去重有效账号
            valid_accounts = list(dict.fromkeys(valid_accounts))

            if valid_accounts:
                middleware.bucketSet(bucket='dd_sf_user', key=user, value=str(valid_accounts))
            else:
                middleware.bucketDel(bucket='dd_sf_user', key=user)

        except Exception as e:
            print(f"处理用户 {user} 时出错: {str(e)}")
            continue

    sender.reply(f"""
=====清理完成=====
✅ 已清理: {cleaned_count}个账号
==================""")


def query_large_coupons(session_id):
    url = "https://mcs-mimp-web.sf-express.com/mcs-mimp/coupon/available/list"

    headers = {
        "Cookie": f"sessionId={session_id}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
    }

    data = {
        "couponType": "",
        "pageNo": 1,
        "pageSize": 100
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if not result.get('success'):
            return "优惠券查询失败"

        coupons = result.get('obj', [])
        if not coupons:
            return "暂无优惠券"

        # 单独显示每张优惠券
        large_coupons = []
        for coupon in coupons:
            try:
                coupon_name = coupon.get('couponName', '未知优惠券')
                expire_time = coupon.get('invalidTm', '')

                # 只筛选包含"免单"字样的优惠券
                if '免单' in coupon_name:
                    coupon_info = f"{coupon_name}, 过期时间: {expire_time}"
                    large_coupons.append(coupon_info)
            except Exception as e:
                print(f"处理优惠券出错: {str(e)}")
                continue

        return '\n'.join(large_coupons) if large_coupons else "暂无免单优惠券"

    except Exception as e:
        print(f"优惠券查询异常: {str(e)}")
        return "优惠券查询失败"


def show_tutorial():
    """显示顺丰插件使用教程"""
    tutorial = """
=====顺丰插件教程=====
🔰 基础功能指令:
------------------
1️⃣ 顺丰登录
• 绑定顺丰账号
• 支持微信扫码/手动链接登录
• 首次使用必须执行

2️⃣ 顺丰查询
• 查看账号积分/蜂蜜
• 查看大额优惠券

3️⃣ 顺丰管理
• 管理已绑定账号
• 授权账号/删除账号
• 支持积分/微信支付

🔧 管理员功能:
------------------
• 顺丰授权: 管理员授权
• 顺丰清理: 清理过期账号

⚠️ 注意事项:
------------------
1. 首次使用请先登录绑定
2. 定期查看账号状态
3. 及时处理授权到期
4. 及时使用满罐蜂蜜
=================="""
    sender.reply(tutorial)


dd_sf_osname, dd_sf_qlname, dd_managecommand, dd_querycommand, dd_signcommand, \
    randommanagecommand, randomquerycommand, randomsigncommand, sfVipmoney, sfcoin, show_point_status, use_ma_pay = getusercontent()
QLurl, qltoken = seekql()
imtype = sender.getImtype()
today_date = datetime.now().date()
today_time = str(today_date)
usermessage = sender.getMessage()
if '登录' in usermessage or '登陆' in usermessage:
    bindaccount()
elif '管理' in usermessage:
    if len(uservalue) != 0:
        meituanmanage()
    else:
        sender.reply(f"""
=====未绑定账号=====
❌ 未找到任何账号信息
💡 发送 {randomsigncommand} 绑定
==================""")
elif '查询' in usermessage:
    if len(uservalue) != 0:
        cxs()
    else:
        sender.reply(f"""
=====未绑定账号=====
❌ 未找到任何账号信息
💡 发送 {randomsigncommand} 绑定
==================""")
elif usermessage == '顺丰清理':
    clean_expired_accounts()
elif usermessage == '顺丰授权':
    sf_auth()
elif usermessage == '顺丰教程':  # 添加教程指令处理
    show_tutorial()
elif imtype == 'fake':
    users = middleware.bucketAllKeys(bucket='dd_sf_user')
    for user in users:
        accountlist = middleware.bucketGet(bucket='dd_sf_user', key=f'{user}')
        accounts = eval(accountlist)
        for account in accounts:
            accurl = middleware.bucketGet(bucket='dd_sf_token', key=f'{account}')
            accountVip = middleware.bucketGet(bucket='dd_sf_auth', key=account)
            try:
                session_id, login_mobile = session_ids(accurl)
            except SystemExit:
                push(user=user, account=account, c="""
⚠️ 账号状态异常
------------------
❌ Cookie已失效
💡 请尽快更新账号""")
                continue
            capacity, usableHoney = Honey(session_id)
            if capacity == '校验未通过':
                continue
            if int(capacity) <= int(usableHoney):
                push(user=user, account=account, c="""
⚠️ 蜂蜜提醒
------------------
🍯 蜂罐已满
💡 请及时使用蜂蜜""")
            if len(accountVip) != 0 and accountVip > today_time:
                continue
            else:
                qlid = allenvs(osname=dd_sf_osname, account=account)
                delenvs(id=qlid)
                push(user=user, account=account, c="""
⚠️ 授权已过期
------------------
❌ 授权状态失效
💡 请及时续费授权""")
else:
    sender.setContinue()
