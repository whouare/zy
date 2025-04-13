import requests
import time
from datetime import datetime
import json

# ==================== 配置部分 ====================
config = {
    'repositories': [
        # GitHub 示例
        {
            'type': 'github',
            'name': 'my_github_repo',
            'owner': 'OWNER',
            'repo': 'REPO_NAME',
            'token': 'YOUR_GITHUB_TOKEN',  # 可选
            'check_interval': 300
        },
        # Gitee 示例
        #https://gitee.com/jdqlscript/zy.git
        {
            'type': 'gitee',
            'name': 'jdqlscript',
            'owner': 'OWNER',
            'repo': 'zy',
            'token': '',  # 可选
            'check_interval': 300
        }
    ],
    'notify': {
        'console': True  # 控制台打印通知
    }
}

STATE_FILE = 'monitor_state.json'


# ==================== 核心代码 ====================
def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)


def get_events(repo_config):
    """获取仓库事件"""
    repo_type = repo_config['type']
    owner = repo_config['owner']
    repo = repo_config['repo']

    if repo_type == 'github':
        url = f"https://api.github.com/repos/{owner}/{repo}/events"
        headers = {'Authorization': f'token {repo_config.get("token", "")}'}
        response = requests.get(url, headers=headers)
    elif repo_type == 'gitee':
        url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/events"
        params = {'access_token': repo_config.get('token', '')}
        response = requests.get(url, params=params)

    response.raise_for_status()
    return response.json()


def process_event(event, repo_config):
    """处理事件并生成消息"""
    event_type = event['type'] if repo_config['type'] == 'github' else event['type']

    # 公共事件处理
    if event_type in ['PushEvent', 'push']:
        commits = event['payload']['commits']
        message = f"新提交: {len(commits)}个提交\n最新提交: {commits[0]['message']}"
    elif event_type in ['WatchEvent', 'star']:
        user = event['actor']['login']
        message = f"用户 {user} star了仓库"
    else:
        message = f"事件类型: {event_type}"

    return message


def monitor():
    state = load_state()

    for repo in config['repositories']:
        repo_name = f"{repo['type']}_{repo['owner']}/{repo['repo']}"
        last_event_id = state.get(repo_name, None)

        try:
            events = get_events(repo)
            new_events = []

            for event in events:
                if event['id'] == last_event_id:
                    break
                new_events.append(event)

            if new_events:
                print(f"\n=== 发现 {len(new_events)} 个新事件 ===")
                for event in reversed(new_events):
                    msg = process_event(event, repo)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] [{repo['name']}] {msg}")

                # 更新状态
                state[repo_name] = new_events[0]['id']
                save_state(state)

        except Exception as e:
            print(f"[{repo['name']}] 监控失败: {str(e)}")


# ==================== 主循环 ====================
if __name__ == "__main__":
    while True:
        monitor()
        sleep_time = min([repo['check_interval'] for repo in config['repositories']])
        time.sleep(sleep_time)