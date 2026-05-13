import sys, os
# sys.path.append(os.path.join(os.path.dirname(__file__), 'utils/move')) # 选择把move文件夹的文件夹的路径传进去
import moveController # 这个是move类的python文件名

moveControl = moveController.MoveController()
if not moveControl.connect():
    print("Could not connect to the robot. Exiting.")

# 可以先登录网页端确保网页端的标记点已经创建好，或者切换到自己的建图(建图确保准确否则可能移动失败)
moveControl.move_to_marker("学校") 