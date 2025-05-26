import bz2
import base64

# 提取并解码base64部分
encoded_data = "xxxx"

# 解密
# 解密 bz2.decompress(base64.b64decode("xxx")))
try:
    # 解码base64
    decoded_data = base64.b64decode(encoded_data)

    # 解压缩bz2
    decompressed_data = bz2.decompress(decoded_data)

    # 转换为字符串并打印
    source_code = decompressed_data.decode('utf-8')
    print("解密后的源代码:")
    print(source_code)

    # 保存到文件以便查看
    with open('decoded_source.py', 'w', encoding='utf-8') as f:
        f.write(source_code)
    print("\n源代码已保存到 decoded_source.py")

except Exception as e:
    print(f"解密过程中出错: {e}")
#
# import bz2, base64, zlib, lzma
#
# exec(bz2.decompress(base64.b64decode(
# )))
#
if __name__ == '__main__':
    APP_NAME = '顺丰速运'
    ENV_NAME = 'SFSF_DW'
    CK_NAME = 'url'
    token = os.getenv(ENV_NAME)
    tokens = token.split('\n')
    print(tokens)
    all_logs = []
    if len(tokens) > 0:

        print(f"\n>>>>>>>>>>共获取到{len(tokens)}个账号<<<<<<<<<<")
        for index, infos in enumerate(tokens):
            run_instance = RUN(infos, index)
            run_result = run_instance.main()
            if run_instance.all_logs:
                all_logs.extend(run_instance.all_logs)
            if not run_result:
                continue
