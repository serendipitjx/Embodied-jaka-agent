import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils/listen'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils/agent'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils/arm'))
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config/lib'))

import voice
import superAgent
import robotControl
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量，注意修改根目录的环境变量
load_dotenv()

class Mission:
    def __init__(self):
        self.voice = voice.Voice(app_id = os.getenv("VOICE_APP_ID"),
                                 api_secret=os.getenv("VOICE_API_SECRET"),
                                 api_key=os.getenv("VOICE_API_KEY"),
                                 duration=5)
        self.agent = superAgent.SuperAgent(tool_path = os.path.join(os.path.dirname(__file__), '..', 'config/jsonDir/tools.json'))
        self.robotcontrol=robotControl.RobotControl()

    def getUserOrder(self) -> str:
        self.voice.record()
        return self.voice.recognize()

    def run(self):
        order = self.getUserOrder()
        if not order:
            print("\033[91m未接收到声音输入或者无法访问互联网来调用云api\033[0m")
        else:
            self.agent.run(order)
        # self.agent.run("请抓取红色物体，放置到1号位置")

if __name__ == '__main__':
    agent = Mission()
    agent.run()
