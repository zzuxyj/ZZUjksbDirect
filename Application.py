# jksbDirect
#
# By Clok Much
import sys
import json
import smtplib
from email.mime.text import MIMEText
from time import sleep

import requests
import urllib3

# 当靠后用户失败时，可考虑增加用户间延迟
users_delay = 38

# ###### 调试区，项目可稳定使用时，两者均应是 False
# 调试开关 正常使用请设定 False ，设定为 True 后会输出更多调试信息，且不再将真实姓名等隐私信息替换为 喵喵喵
debug_switch = False
# 总是认为上报失败的标记 正常使用请设定为 False ，设定为 True 后会每次都发送失败邮件，即使是上报成功
always_fail = False

# 开始时接收传入的 Secrets
mail_id = sys.argv[1]
mail_pd = sys.argv[2]
processing_pool = sys.argv[3]

# mail_id = "x6sfHZ6h4X53hCU6q435thqryqkcqe9x969n@outlook.com"
# mail_pd = "IA6ZM6E5VnkJqIMpq6aCD2I6RnUgeUx"
# processing_pool = "2029788745693，eG4k%QgDF2KzF#M，2625，黑龙江省.风来市.火星蔬菜种植基地，凌墨，3，septemberRecever2413@qq.com，WeaknessSoreCentralConfirmed"
# 第 3 个参数传递多用户填报信息，格式如下：
# "学号，密码，城市码，地理位置，真实姓名，反馈邮箱（接收邮件），可选的疫苗接种情况，可选的症状或特定情况描述！学号2，密码2，城市码2，地理位置2..."
# 以中文逗号分隔，子项目不得包含中文逗号和中文感叹号，每个用户以中文感叹号分割

# 禁用不安全链接的警告
urllib3.disable_warnings()

# 分割多用户列表解析
if "！" in processing_pool:
    # 去除末尾分割多用户符号，仅检查、去除一次
    if processing_pool[-1] == "！":
        processing_pool = processing_pool[:-1]
    user_pool = processing_pool.split("！")
    print("当前用户数量为 " + str(len(user_pool)))
else:
    user_pool = [processing_pool]

# 对单个用户进行循环
now_user = 0
for pop_user in user_pool:
    now_user += 1
    this_one = True
    this_user = pop_user.split("，")
    # 单个用户信息检查
    if len(this_user) < 6:
        print("用户" + str(now_user) + "池配置有误，请参照说明重新配置！此用户信息条目数量少于6，需要填写的条目数至少为6，可能是将分割的中文逗号输入为英文逗号，此用户配置将被忽略.")
        continue
    if len(this_user[2]) != 4:
        print("用户" + str(now_user) + "城市码描述有误，正确的长度应该是4，当前长度为" + str(len(this_user[2])) + '，此用户将被跳过.')
        continue
    user_id = this_user[0]
    user_pd = this_user[1]
    city_code = this_user[2]
    if "@" in this_user[3]:
        # 若存在需要修正 memo22 显示位置的配置，则解析
        location = this_user[3].split("@")[0]
        location_get = this_user[3].split("@")[1]
    else:
        location = this_user[3]
        location_get = False
    real_name = this_user[4]
    mail_target = this_user[5]
    # 读取开放表单数据
    with open("config.json", "rb") as file_obj:
        public_data = json.load(file_obj)
        file_obj.close()
    # 读取描述文件
    with open("description.json", "rb") as file_obj:
        description = json.load(file_obj)
        file_obj.close()
    # 修改 公开表单默认值 为 特定值
    public_data['myvs_13a'] = city_code[:2]
    public_data['myvs_13b'] = city_code
    public_data['myvs_13c'] = location
    # 解析条目长度为 7 时的情况
    if len(this_user) == 7:
        if (this_user[6] == "1") or (this_user[6] == "2") or (this_user[6] == "3") or (this_user[6] == "4"):
            public_data['myvs_26'] = this_user[6]
        else:
            for descr in description["symbols"]:
                if descr in this_user[6].lower():
                    public_data[description[descr][0]] = description[descr][1]
    # 解析条目长度为 8 时的情况
    if len(this_user) == 8:
        if (this_user[6] == "1") or (this_user[6] == "2") or (this_user[6] == "3") or (this_user[6] == "4"):
            public_data['myvs_26'] = this_user[6]
        for descr in description["symbols"]:
            if descr in this_user[7].lower():
                public_data[description[descr][0]] = description[descr][1]
    if location_get:
        public_data['memo22'] = location_get
    # 提前对指示标记进行赋值，避免处理异常时跳过赋值导致变量未定义错误
    step_1_calc = 0
    step_1_output = ""
    step_1_state = False
    step_2_calc = 0
    step_2_output = ""
    step_2_state = False
    step_3_calc = 0
    step_3_output = ""
    step_3_state = False
    result = ""
    result_flag = 0
    response = False
    mixed_token = False
    all_input = sys.argv
    sleep(users_delay)   # 每个用户之间延时，以提高成功率

    # 创建发送邮件的方法
    def report_mail(full_info=debug_switch):
        if full_info:
            this_time_vars = {'result_flag': result_flag,
                              'mixed_token': mixed_token,
                              'public_data': public_data,
                              'step_1_output': step_1_output,
                              'step_1_calc': step_1_calc,
                              'step_1_state': step_1_state,
                              'step_2_output': step_2_output,
                              'step_2_calc': step_2_calc,
                              'step_2_state': step_2_state,
                              'step_3_output': step_3_output,
                              'step_3_calc': step_3_calc,
                              'step_3_state': step_3_state,
                              'secrets_inputted': sys.argv,
                              'pop_user': pop_user,
                              'step_1_post_data': post_data,
                              'result': result
                              }
        else:
            this_time_vars = {'result_flag': result_flag,
                              'step_1_output': step_1_output.replace(real_name, "喵喵喵").replace(user_id, "喵喵喵"),
                              'step_1_calc': step_1_calc,
                              'step_1_state': step_1_state,
                              'step_2_calc': step_2_calc,
                              'step_2_state': step_2_state,
                              'step_3_calc': step_3_calc,
                              'step_3_output': step_3_output.replace(real_name, "喵喵喵").replace(user_id, "喵喵喵"),
                              'step_3_state': step_3_state,
                              'result': result.replace(real_name, "喵喵喵").replace(user_id, "喵喵喵")
                              }
        with open("mail_public_config.json", 'rb') as file_obj_inner:
            public_mail_config = json.load(file_obj_inner)
            file_obj_inner.close()
        # 配置邮件内容
        mail_message = MIMEText(str(this_time_vars), 'plain', 'utf-8')
        mail_message['Subject'] = public_mail_config['title']
        mail_message['From'] = mail_id
        mail_message['To'] = mail_target
        # 尝试发送邮件
        try:
            mail_host = "Zero"
            mail_port = "0"
            this_host = "Zero"
            for each_host in public_mail_config["symbol"]:
                if each_host in mail_id:
                    mail_host = public_mail_config[each_host]["host"]
                    mail_port = public_mail_config[each_host]["port"]
                    this_host = each_host
                    break
            if mail_host == "Zero":
                print('发送结果的邮箱设置异常，请在 mail_public_config.json 中检查邮箱的域名配置，以及发信SMTP服务器配置.')
                raise smtplib.SMTPException
            if this_host == "Zero":
                print('发送结果的邮箱设置异常，请确保 mail_public_config.json 中包含您的邮箱配置.')
                raise smtplib.SMTPException
            if "encryption" in public_mail_config[this_host].keys():
                smtp_obj = smtplib.SMTP(mail_host, mail_port)
                smtp_obj.ehlo()
                smtp_obj.starttls()
                smtp_obj.ehlo()
                smtp_obj.login(mail_id, mail_pd)
                if full_info:
                    smtp_obj.sendmail(mail_id, mail_id, mail_message.as_string())
                else:
                    smtp_obj.sendmail(mail_id, mail_target, mail_message.as_string())
                smtp_obj.quit()
                print('用户' + str(now_user) + '具体提示信息已发送到邮箱，内容包含个人敏感信息，请勿泄露邮件内容.')
            else:
                smtp_obj = smtplib.SMTP_SSL(mail_host, mail_port)
                smtp_obj.login(mail_id, mail_pd)
                if full_info:
                    smtp_obj.sendmail(mail_id, mail_id, mail_message.as_string())
                else:
                    smtp_obj.sendmail(mail_id, mail_target, mail_message.as_string())
                smtp_obj.quit()
                print('用户' + str(now_user) + '具体提示信息已发送到邮箱，内容包含个人敏感信息，请勿泄露邮件内容.')
            if now_user >= len(user_pool):
                print("所有用户遍历完毕，结束运行.")
                exit(0)
            else:
                return "next_one"
        except smtplib.SMTPException:
            print('发送结果的邮箱设置可能异常，请检查邮箱和密码配置，以及发信SMTP服务器配置.')
            raise smtplib.SMTPException


    # 准备请求数据
    session = requests.session()
    info = {}
    header = {"Origin": "https://jksb.v.zzu.edu.cn",
              "Referer": "https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/first0",
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/97.0.4692.71 Safari/537.36",
              "Host": "jksb.v.zzu.edu.cn"
              }
    post_data = {"uid": user_id,
                 "upw": user_pd,
                 "smbtn": "进入健康状况上报平台",
                 "hh28": "722",
                 }
    step_2_data = {'day6': 'b',
                   'did': '1',
                   'men6': 'a'
                   }

    # 第一步 获取 token
    while step_1_calc < 4:
        try:
            # 接收回应数据
            response = session.post("https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/login", data=post_data,
                                    headers=header,
                                    verify=False)
            if type(response) == requests.models.Response:
                response.encoding = "utf-8"
                step_1_output = response.text
                if "验证码" in step_1_output:
                    print('用户' + str(now_user) + "运行时返回需要验证码，将终止本次打卡，您需要在 Action 中合理配置运行时间.")
                    exit(1)
                mixed_token = response.text[response.text.rfind('ptopid'):response.text.rfind('"}}\r''\n</script>')]
                if "hidden" in mixed_token:
                    step_1_calc += 1
                    continue
                elif not mixed_token:
                    step_1_calc += 1
                    continue
                else:
                    token_ptopid = mixed_token[7:mixed_token.rfind('&sid=')]
                    token_sid = mixed_token[mixed_token.rfind('&sid=') + 5:]
                    step_1_state = True
                    public_data['ptopid'] = token_ptopid
                    step_2_data['ptopid'] = token_ptopid
                    public_data['sid'] = token_sid
                    step_2_data['sid'] = token_sid
                    break
            else:
                if step_1_calc < 3:
                    step_1_calc += 1
                    print('用户' + str(now_user) + "获取 token 中" + str(step_1_calc)
                          + "次失败，没有response，可能学校服务器故障，或者学号或密码有误，请检查返回邮件信息.")
                    continue
                else:
                    print('用户' + str(now_user) + "获取 token 中" + str(step_1_calc)
                          + "次失败，没有response，可能学校服务器故障，或者学号或密码有误，次数达到预期，终止本次打卡，报告失败情况.")
                    if report_mail(debug_switch) == "next_one":
                        this_one = False
                        break
        except requests.exceptions.SSLError:
            if step_1_calc < 3:
                step_1_calc += 1
                print('用户' + str(now_user) + "获取 token 中" + str(step_1_calc)
                      + "次失败，服务器提示SSLError，可能与连接问题有关.")
                continue
            else:
                print('用户' + str(now_user) + "获取 token 中" + str(step_1_calc)
                      + "次失败，服务器提示SSLError，次数达到预期，终止本次打卡，报告失败情况.")
                if report_mail(debug_switch) == "next_one":
                    this_one = False
                    break

    # 第二步 提交填报人
    header["Referer"] = 'https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb'
    # response = False
    while step_2_calc < 4:
        if not this_one:
            break
        try:
            # 获取 fun18 的值
            mixed_url = 'https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb?ptopid=' + token_ptopid + '&sid=' + token_sid + '&fun2='
            jksb_blank = session.get(mixed_url, headers=header,
                                     verify=False)
            if type(jksb_blank) == requests.models.Response:
                jksb_blank.encoding = "utf-8"
                fun18_value = jksb_blank.text[jksb_blank.text.rfind('input type="hidden" name="fun18" value="') + 40:jksb_blank.text.rfind('" /><input type="hidden" name="sid"')]
                step_2_data["fun18"] = fun18_value
                public_data["fun18"] = fun18_value
            else:
                if step_2_calc < 3:
                    step_2_calc += 1
                    print('用户' + str(now_user) + "提交填报人（获取 fun18）" + str(step_2_calc)
                          + "次失败，没有response，可能学校服务器故障，或者学号或密码有误，请检查返回邮件信息.")
                    continue
                else:
                    print('用户' + str(now_user) + "提交填报人（获取 fun18）" + str(step_2_calc)
                          + "次失败，没有response，可能学校服务器故障，次数达到预期，终止用户"
                          + str(now_user) + "打卡，报告失败情况.")
                    if report_mail(debug_switch) == "next_one":
                        this_one = False
                        break
            # 获取填报表单
            response = session.post('https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb', headers=header,
                                    data=step_2_data,
                                    verify=False)
            if type(response) == requests.models.Response:
                response.encoding = "utf-8"
                step_2_output = response.text
                if "发热" in step_2_output:
                    step_2_state = True
                    break
                elif "无权" in step_2_output:
                    print('用户' + str(now_user) + "提交填报人" + str(step_2_calc)
                          + "次失败，可能是学号或密码有误，或是间隔过短致需要验证码，终止用户" + str(now_user) + "打卡，报告失败情况.")
                    if report_mail(debug_switch) == "next_one":
                        this_one = False
                        break
                elif "验证码" in step_2_output:
                    print('用户' + str(now_user) + "提交填报人" + str(step_2_calc)
                          + "次失败，服务器返回需要验证码，可能是请求过于频繁，终止用户"
                          + str(now_user) + "打卡，报告失败情况.")
                    if report_mail(debug_switch) == "next_one":
                        this_one = False
                        break
                else:
                    print('用户' + str(now_user) + "提交填报人" + str(step_2_calc)
                          + "次失败，返回内容在 else ，原因未知，终止用户" + str(now_user) + "打卡，报告失败情况.")
                    if report_mail(debug_switch) == "next_one":
                        this_one = False
                        break
            else:
                if step_2_calc < 3:
                    step_2_calc += 1
                    print('用户' + str(now_user) + "提交填报人" + str(step_2_calc)
                          + "次失败，没有response，可能学校服务器故障，或者学号或密码有误，请检查返回邮件信息.")
                    continue
                else:
                    print('用户' + str(now_user) + "提交填报人" + str(step_2_calc)
                          + "次失败，没有response，可能学校服务器故障，次数达到预期，终止用户"
                          + str(now_user) + "打卡，报告失败情况.")
                    if report_mail(debug_switch) == "next_one":
                        this_one = False
                        break
        except requests.exceptions.SSLError:
            if step_2_calc < 3:
                step_2_calc += 1
                print('用户' + str(now_user) + "提交填报人" + str(step_2_calc)
                      + "次失败，服务器提示SSLError，可能与连接问题有关.")
                continue
            else:
                print('用户' + str(now_user) + "提交填报人" + str(step_2_calc)
                      + "次失败，服务器提示SSLError，次数达到预期，终止用户"
                      + str(now_user) + "本次打卡，报告失败情况.")
                if report_mail(debug_switch) == "next_one":
                    this_one = False
                    break

    # 第三步 提交表格
    # response = False
    while step_3_calc < 4:
        if not this_one:
            break
        try:
            response = session.post('https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb', headers=header,
                                    data=public_data,
                                    verify=False)
            if type(response) == requests.models.Response:
                response.encoding = "utf-8"
                step_3_output = response.text
                if ("感谢你今日上报" in step_3_output) or ("感谢您今日上报" in step_3_output):
                    step_3_state = True
                    break
                else:
                    print('用户' + str(now_user) + "提交表格中" + str(step_3_calc)
                          + "次失败，可能打卡平台增加了新内容，或是用户"
                          + str(now_user) + "今日打卡结果已被审核而不能再修改，请检查返回邮件信息（第三步回应内容不包含成功提示）.")
                    if report_mail(debug_switch) == "next_one":
                        this_one = False
                        break
            else:
                if step_3_calc < 3:
                    step_3_calc += 1
                    print('用户' + str(now_user) + "提交表格中" + str(step_3_calc)
                          + "次失败，没有response，可能学校服务器故障，或者用户"
                          + str(now_user) + "学号或密码有误，请检查返回邮件信息.")
                    continue
                else:
                    print('用户' + str(now_user) + "提交表格中" + str(step_3_calc)
                          + "次失败，没有response，可能学校服务器故障，次数达到预期，终止用户"
                          + str(now_user) + "打卡，报告失败情况.")
                    if report_mail(debug_switch) == "next_one":
                        this_one = False
                        break
        except requests.exceptions.SSLError:
            if step_3_calc < 3:
                step_3_calc += 1
                print('用户' + str(now_user) + "提交表格中" + str(step_3_calc)
                      + "次失败，服务器提示SSLError，可能与连接问题有关.")
                continue
            else:
                print('用户' + str(now_user) + "提交表格中" + str(step_3_calc)
                      + "次失败，服务器提示SSLError，次数达到预期，终止用户"
                      + str(now_user) + "打卡，报告失败情况.")
                if report_mail(debug_switch) == "next_one":
                    this_one = False
                    break
    # 关闭 session 以玄学提高成功率
    try:
        session.close()
        del session
    except AttributeError:
        print('用户' + str(now_user) + "未被建立便被请求关闭，但关闭请求已被忽略.")
    except NameError:
        print('用户' + str(now_user) + "不存在但被请求回收/消除，但回收/消除请求已被忽略.")
    # 分析上报结果
    if not this_one:
        continue
    result = step_3_output
    if ("感谢你今日上报" in result) or ("感谢您今日上报" in result):
        result_flag = True
        # signed_json['signed'].append(now_user - 1)  # 打卡完成，记录入json
        print("用户" + str(now_user) + "上报成功")
    elif "审核" in result:
        result_flag = False
        print("注意：用户" + str(now_user) + "上报失败！！返回提示今日已被审核，不能再上报.")
        if report_mail(debug_switch) == "next_one":
            this_one = False
            break
    elif "由于如下原因" in result:
        result_flag = False
        print("注意：用户" + str(now_user) + "上报失败！！返回提示有原因导致上报失败，可能是新增了项目，可能需要更新.")
        if report_mail(debug_switch) == "next_one":
            this_one = False
            break
    elif "重新登录" in result:
        result_flag = False
        print("注意：用户" + str(now_user) + "上报失败！！可能是用户名或密码错误，或服务器响应超时，返回需要重新登录.")
        if report_mail(debug_switch) == "next_one":
            this_one = False
            break
    else:
        result_flag = False
        print("注意：用户" + str(now_user) + "上报失败！！原因未知，请自行检查返回结果和邮件中的变量输出.")
        if report_mail(debug_switch) == "next_one":
            this_one = False
            break

    # 总是发送邮件设定为 True 时，发送邮件
    if always_fail:
        report_mail(debug_switch)

