

# 笨笨诈骗版 果派-中医
# https://fqzw0h.vip.xvnn.cn/onboarding.html?id=d6a22fb2b5f3a675a3c51b624d789b4b
# 两个变量 一个GuoUser  一行一个openid放进去几科
# 一个GuoTaskId  写活动id  以上面的链接为例子 id就是d6a22fb2b5f3a675a3c51b624d789b4b
# 一天0.6
# 有问题请及时联系笨笨 v:Bbvip666a （有其他想要的脚本也可以联系，尽量试着写一写）
#
# Expecting value: line 1 column 1 (char 0) 报错请求频繁 过段时间重试即可
#
#   --------------------------------祈求区--------------------------------
#                     _ooOoo_
#                    o8888888o
#                    88" . "88
#                    (| -_- |)
#                     O\ = /O
#                 ____/`---'\____
#               .   ' \| |// `.
#                / \||| : |||// #              / _||||| -:- |||||- #                | | \\ - /// | |
#              | \_| ''\---/'' | |
#               \ .-\__ `-` ___/-. /
#            ___`. .' /--.--\ `. . __
#         ."" '< `.___\_<|>_/___.' >'"".
#        | | : `- \`.;`\ _ /`;.`/ - ` : | |
#          \ \ `-. \_ __\ /__ _/ .-` / /
#  ======`-.____`-.___\_____/___.-`____.-'======
#                     `=---='
#
#  .............................................
#           佛祖保佑             永无BUG
#           佛祖镇楼             BUG辟邪
#   --------------------------------代码区--------------------------------

import zlib
import base64
exec(zlib.decompress(base64.b64decode("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".encode('utf-8'))).decode('utf-8'))
