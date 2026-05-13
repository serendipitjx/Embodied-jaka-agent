#!/usr/bin/env python3
# coding: utf-8
import socket
import json
import jkrc
import time
import threading
import sys
import signal

# 定义预设点位 (请根据您的实际机器人配置进行修改)
# 关节角度，单位：rad
HOME_JOINT = [0.0, -0.78, 1.57, 0.0, 1.57, 0.0]  # 假设的 Home 点
PICK_READY_JOINT = [0.5, -0.5, 1.0, 0.0, 1.0, 0.5] # 抓取准备点
PLACE_READY_JOINT = [-0.5, -0.5, 1.0, 0.0, 1.0, -0.5] # 放置准备点

# 末端工具坐标，单位：mm/rad
# PICK_POINT_XYZRPY = [400, 100, 50, 0, 1.57, 0] # 抓取位置
# PLACE_POINT_XYZRPY = [400, -100, 50, 0, 1.57, 0] # 放置位置


class RobotServer:  # 🚀 修改点 1: 类名改为 RobotServer，匹配 superAgent.py
    def __init__(self, robot_ip="192.168.10.90"):
        # 初始化机器人
        try:
            self.robot = jkrc.RC(robot_ip)
            self.robot.login()
            print("[ARM] 机械臂登录成功")
            self.robot.power_on()
            self.robot.enable_robot()
            print("[ARM] 机械臂已使能")
            self.is_connected = True
        except Exception as e:
            print(f"[ARM] 机械臂初始化失败: {e}")
            self.is_connected = False
            # 退出程序或设置一个模拟模式

    def joint_move(self, joint_pos, move_mode=0, is_block=True, speed=1.0):
        """控制机器人进行关节运动。"""
        if not self.is_connected:
            print("[ARM-SIM] 模拟关节移动")
            return 0
        return self.robot.joint_move(joint_pos, move_mode, is_block, speed)
    
    def linear_move(self, end_pos, move_mode=0, is_block=True, speed=500):
        """控制机器人进行末端直线运动。"""
        if not self.is_connected:
            print("[ARM-SIM] 模拟直线移动")
            return (0,)
        return self.robot.linear_move(end_pos, move_mode, is_block, speed)

    def get_pos(self):
        """获取关节角度"""
        if not self.is_connected:
            return HOME_JOINT
        ret = self.robot.get_joint_position()
        if ret[0] == 0:  
            return ret[1]
        else:  
            return ret[0]

    def suck(self):
        """执行吸取动作"""
        print("[ARM] 执行吸取（DO 1=1）")
        if not self.is_connected:
            time.sleep(3)
            return
        self.robot.set_digital_output(iotype = 1, index = 1, value = 1)
        time.sleep(3)

    def release(self):
        """执行释放动作"""
        print("[ARM] 执行释放（DO 1=0）")
        if not self.is_connected:
            time.sleep(2)
            return
        self.robot.set_digital_output(iotype = 1, index = 1, value = 0)
        time.sleep(2)

    # 🚀 修改点 2: 实现 pickAndPlace 函数
    def pickAndPlace(self, color: str, number: str) -> str:
        """
        根据颜色和编号抓取物体并放置。
        这个是 superAgent.py 调用的主要函数。
        """
        print(f"\n[ARM-TASK] 接收到任务：抓取 {number} 个 {color} 物体并放置。")
        
        if not self.is_connected:
            return "抓取失败: 机械臂未连接或初始化失败。"
        
        # 1. 移动到抓取准备点
        print("[ARM-TASK] 1. 移动到抓取准备点...")
        ret = self.joint_move(PICK_READY_JOINT, speed=1.5)
        if ret != 0: return f"抓取失败: 移动到准备点失败 (Err:{ret})"

        # 2. 假设抓取位置是固定的，向下直线移动
        # 实际应用中，这里需要加入视觉定位，获取目标物体(color, number)的精确坐标
        print("[ARM-TASK] 2. 直线下降到抓取点...")
        # 假设通过视觉获取了目标末端位置 (XYZRPY)
        PICK_POINT_XYZRPY = self.robot.get_tool_position()[1] # 获取当前位置作为示例
        PICK_POINT_XYZRPY[2] -= 100 # Z轴向下移动100mm
        ret = self.linear_move(PICK_POINT_XYZRPY, speed=200)
        if ret[0] != 0: return f"抓取失败: 直线下降失败 (Err:{ret[0]})"
        
        # 3. 吸取物体
        self.suck()
        
        # 4. 垂直抬升，回到抓取准备点
        print("[ARM-TASK] 4. 垂直抬升...")
        PICK_POINT_XYZRPY[2] += 100 # Z轴向上移动100mm
        ret = self.linear_move(PICK_POINT_XYZRPY, speed=200)
        if ret[0] != 0: return f"抓取失败: 垂直抬升失败 (Err:{ret[0]})"
        
        # 5. 移动到放置准备点
        print("[ARM-TASK] 5. 移动到放置准备点...")
        ret = self.joint_move(PLACE_READY_JOINT, speed=1.5)
        if ret != 0: return f"抓取失败: 移动到放置准备点失败 (Err:{ret})"

        # 6. 直线下降到放置点
        print("[ARM-TASK] 6. 直线下降到放置点...")
        PLACE_POINT_XYZRPY = self.robot.get_tool_position()[1] # 获取当前位置作为示例
        PLACE_POINT_XYZRPY[2] -= 100 # Z轴向下移动100mm
        ret = self.linear_move(PLACE_POINT_XYZRPY, speed=200)
        if ret[0] != 0: return f"抓取失败: 直线下降放置点失败 (Err:{ret[0]})"
        
        # 7. 释放物体
        self.release()

        # 8. 垂直抬升
        print("[ARM-TASK] 8. 垂直抬升...")
        PLACE_POINT_XYZRPY[2] += 100 # Z轴向上移动100mm
        ret = self.linear_move(PLACE_POINT_XYZRPY, speed=200)
        if ret[0] != 0: return f"抓取失败: 垂直抬升失败 (Err:{ret[0]})"
        
        # 9. 回到 Home 点
        print("[ARM-TASK] 9. 返回 Home 点...")
        self.joint_move(HOME_JOINT, speed=1.5)

        return "抓取成功"

# 示例自测代码
if __name__ == "__main__":
    try:
        robot_server = RobotServer()
        print(robot_server.get_pos())
        
        # 测试 pickAndPlace 功能
        result = robot_server.pickAndPlace("红色", "一个")
        print(f"\nPickAndPlace 最终结果: {result}")
        
    except Exception as e:
        print(f"主程序异常: {e}")