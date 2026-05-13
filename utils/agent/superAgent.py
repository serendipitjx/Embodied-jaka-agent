import os
import sys
import time
import platform
import subprocess
import json

from volcenginesdkarkruntime import Ark
from volcenginesdkarkruntime.types.chat import ChatCompletion
from dotenv import load_dotenv


sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'move'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'arm'))
# sys.path.append(os.path.join(os.path.dirname(__file__), '../..', '/config/lib'))
import moveController
# import armControl
import armTest

class SuperAgent:
    def __init__(self, tool_path = os.path.join(os.path.dirname(__file__), '../..', 'config/jsonDir/tools.json')):
        # 类初始化
        self.moveController = moveController.MoveController()
        # 加载 .env 文件中的环境变量，注意修改根目录的环境变量
        load_dotenv()
        self.client = Ark()

        # 工具初始化
        self.tool_path = tool_path
        
        # TCP
        # self.armControl = armControl.RobotServer()
        self.armControl = armTest.RobotServer()
        while not self.moveController.connect():
            print("\033[93mCould not connect to the robot. Retrying in 2 seconds...\033[0m")
            time.sleep(2)  # 等待3秒后再次尝试连接

        while not self.can_ping("8.8.8.8"):
            print("\033[93mCould not connect to the Internet. Retrying in 2 seconds...\033[0m")
            time.sleep(2)  # 等待3秒后再次尝试连接

        self.system_prompt = """你是一个协作机器人，你有以下的功能：
                    1. 取消移动
                    2. 移动到预先设置的点位
                    3. 抓取物体并且放置
                    """


        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.tools = self._load_tools()
        

        # 变量初始化
        self.move_connected = False
        if self.moveController.connect():
            self.move_connected = True
            print("机器人底盘初始化成功")

    def can_ping(self, ip: str, timeout_s: float = 2.0) -> bool:
        """
        跨平台 ping 检查（Windows/macOS/Linux），
        通过 subprocess 的 timeout 控制等待时长，不依赖 ping 的 -W/-w 细节。
        """
        is_windows = platform.system().lower() == "windows"
        count_flag = "-n" if is_windows else "-c"
        cmd = ["ping", count_flag, "1", ip]

        try:
            # 超过 timeout_s 没有返回就认定为失败
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=timeout_s
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False

    
    def _load_tools(self):
        """从 JSON 文件加载工具定义"""
        with open(self.tool_path, "r", 
                  encoding="utf-8") as f:
            return json.load(f)
        
    def is_cancel_intent(self, text: str) -> bool:
        """
        简单的关键词检测：如果用户话语中包含“取消/停止/中止/abort/stop”等词，
        就认为是取消移动意图。你可以根据需要拓展或改成意图分类器。
        """
        if not text:
            return False
        t = text.lower()
        cancel_keywords = [
            "取消", "停止", "中止", "abort", "stop", "cancel", "不要移动",
            "不要", "终止", "停止移动"
        ]
        for kw in cancel_keywords:
            if kw in t:
                return True
        return False

    def add_user_message(self, content: str):
        # self.messages = [{"role": "system", "content": self.system_prompt}]
        self.order = content
        self.messages = [{"role": "system", "content": self.system_prompt},
                 {"role": "user", "content": str(content)}]
        
        # 预先构建请求模板，但不执行
        self.request_params = {
            "model": "deepseek-v3-1-250821", # "doubao-seed-1-6-flash-250715", "deepseek-r1-250528", "deepseek-v3-1-250821"
            "messages": self.messages,
            "tools": self.tools,
            # "thinking": {"type": "auto"} #  auto disabled enabled
        }

        # print(f"self.messages: {self.messages}")

        

    def _execute_tool_calls(self):
        # while True:
        completion: ChatCompletion = self.client.chat.completions.create(**self.request_params)
        response = completion.choices[0].message

        # print(f"response: {response}")

        if completion.choices[0].finish_reason == "tool_calls":
            # self.messages.append(response.model_dump())
            tool_calls = response.tool_calls

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                print(f"🔧 执行工具: {tool_name}")

                try:
                    arguments = json.loads(tool_call.function.arguments)
                except:
                    print(f"⚠️ 工具 {tool_name} 参数解析失败: {tool_call.function.arguments}")
                    arguments = {}

                if self.is_cancel_intent(self.order) and tool_name == "move_to_location":
                    print("⚠️ 检测到用户意图为取消，但模型尝试移动。已拦截该移动请求，改为执行 cancel_move。")
                    try:
                        tool_result = self.moveController.cancel_move()
                        print(f"cancel_move result: {tool_result}")
                    except Exception as e:
                        print(f"执行 cancel_move 时发生错误: {e}")
                    # 跳过执行模型原本的 move_to_location
                    continue

                if tool_name == "move_to_location":
                    location_name = arguments.get("location_name", "")
                    if location_name == "": # 如果没有提取到移动地点就取消移动
                        continue
                    tool_result = self.moveController.move_to_marker(location_name)

                elif tool_name == "cancel_move":
                    tool_result = self.moveController.cancel_move()

                elif tool_name == "pickAndPlace":
                    color = arguments.get("color", "")
                    number = arguments.get("number", "")
                    tool_result = self.armControl.pickAndPlace(color, number)
                    if tool_result == "抓取失败":
                        print("抓取失败")
                        # break
                    print("抓取成功")

                else:
                    print(f"❌ 未知的工具函数: {tool_name}")
                    # break

                # self.messages.append({
                #     "role": "tool",
                #     "content": str(tool_result) if tool_result else f"{tool_name} 执行完成，但返回空",
                #     "tool_call_id": tool_call.id
                # })

        elif completion.choices[0].finish_reason == "stop":
            print("模型回复:", response.content)
            # break

    def run(self, userMsg):
        self.add_user_message(userMsg)
        self._execute_tool_calls()
               
import sys, os
# sys.path.append(os.path.join(os.path.dirname(__file__), 'utils/move')) # 选择把move文件夹的文件夹的路径传进去
     
'''if __name__ == '__main__':
    superAgent = SuperAgent()
    superAgent.run("请前往工作间")
    moveControl = moveController.MoveController()
    if not moveControl.connect():
        print("Could not connect to the robot. Exiting.")'''

    # 可以先登录网页端确保网页端的标记点已经创建好，或者切换到自己的建图(建图确保准确否则可能移动失败)
    # moveControl.move_to_marker("客厅") 
