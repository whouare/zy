
import requests

import requests
from requests.exceptions import RequestException


def main():
    # 创建会话对象，自动管理cookies
    session = requests.Session()

    # 创建请求参数
    data = {
        "token": "8c421b1ce5e61cb4478e172fd7a3ee1d",
        "email": "kingjpren@foxmail.com",
        "password": "7m3fyiKduBM7KDp"
    }

    try:
        # 发送POST请求
        response = session.post(
            "https://www.iimyun.com/login?action=email",
            data=data,
            timeout=10  # 设置超时时间
        )

        # 检查HTTP状态码
        response.raise_for_status()

        # 打印响应内容
        print("登录成功! 会话已建立.")
        print(f"状态码: {response.status_code}")
        print(f"获取的cookies: {session.cookies}")
        print("\n响应内容:")
        print(response.text)

        # 示例：使用已登录的会话继续访问需要权限的页面
        protected_page = session.get("https://www.iimyun.com/dashboard")
        print("\n访问受保护页面:")
        print(protected_page.text)

    except RequestException as e:
        print(f"请求发生错误: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")
    finally:
        # 关闭会话
        session.close()


if __name__ == "__main__":
    main()