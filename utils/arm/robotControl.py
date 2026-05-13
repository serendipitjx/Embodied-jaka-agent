#!/usr/bin/env python3
# coding: utf-8
import socket
import json
import jkrc
import time
import threading
import sys
import signal

class RobotControl:
    def __init__(self, robot_ip="192.168.10.90"):
        # 初始化机器人
        self.robot = jkrc.RC(robot_ip)
        self.robot.login()
        print("[ROBOT] Successfully logged in")
        self.robot.power_on()
        print("[ROBOT] Robot powered on")
        self.robot.enable_robot()
        print("[ROBOT] Robot enabled")

    def joint_move(self, joint_pos, move_mode, is_block, speed):
        """
        具体查看 https://www.jaka.com/docs/guide/SDK/Python.html#%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%85%B3%E8%8A%82%E8%BF%90%E5%8A%A8
        控制机器人进行关节运动。

        Args:
            joint_pos (list[float]): 机器人关节运动目标位置。
            move_mode (int): 0 代表绝对运动，1 代表相对运动。
            is_block (bool): 是否阻塞调用。True 表示机器人运动完成才返回，False 表示接口调用完成立即返回。
            speed (float): 机器人关节运动速度，单位：rad/s。

        Returns:
            int: 返回错误码（0 表示成功），或根据 SDK 定义返回执行状态。
        """
        return self.robot.joint_move(joint_pos, move_mode, is_block, speed)
    
    def linear_move(self, end_pos, move_mode, is_block, speed):
        """
        具体查看 https://www.jaka.com/docs/guide/SDK/Python.html#%E6%9C%BA%E5%99%A8%E4%BA%BA%E6%9C%AB%E7%AB%AF%E7%9B%B4%E7%BA%BF%E8%BF%90%E5%8A%A8
        控制机器人进行末端直线运动。

        Args:
            end_pos (list[float]): 机器人末端运动目标位置。
            move_mode (int): 运动模式。0 表示绝对运动，1 表示相对运动。
            is_block (bool): 是否阻塞调用。True 表示机器人运动完成后才返回；
                False 表示接口调用完成立即返回。
            speed (float, optional): 机器人直线运动速度，单位 mm/s，默认 500 mm/s。

        Returns:
            tuple: 
                成功返回 `(0,)`，失败返回其他错误码（SDK 定义为元组格式）。
        """
        	#运动模式  
        return self.robot.linear_move(end_pos, move_mode, is_block, speed)

    def get_pos(self):
        ret = self.robot.get_joint_position()
        if ret[0] == 0:  
            return ret[1]
        else:  
            return ret[0] # 获取关节角度失败

    def suck(self):
        self.robot.set_digital_output(iotype = 1,  index = 1,  value = 1)
        time.sleep(3)

    def release(self):
        self.robot.set_digital_output(iotype = 1,  index = 1,  value = 0)
        time.sleep(2)
    
if __name__ == "__main__":
    robot = RobotControl()
    joint_pos = robot.get_pos()
    print(joint_pos)
    robot.joint_move([2.5,-1.0,1.5,-1,-0.3,1.0],0,True,speed=1)
    robot.suck()
    robot.release()
