#!/usr/bin/env python3
import snowboydecoder
import sys
import signal

# 全局变量用于控制程序退出
interrupted = False


def signal_handler(signal, frame):
    """
    处理 Ctrl+C 信号，设置为中断状态
    """
    global interrupted
    interrupted = True
    print("\n👋 用户手动停止监听...")


def interrupt_callback():
    """
    供 Snowboy 调用的回调函数，检查是否需要停止循环
    """
    global interrupted
    return interrupted


def detected_and_stop_callback():
    """
    🚀 修改点 1: 唤醒词被检测到时执行的回调函数。
    - 播放提示音
    - 设置中断标志，以便退出主循环
    """
    global interrupted
    
    # 1. 执行原有的播放提示音操作
    print("✨ 唤醒词已检测到！正在停止监听...")
    snowboydecoder.play_audio_file()
    
    # 2. 停止监听主循环
    interrupted = True


# --- 主程序逻辑 ---

if len(sys.argv) == 1:
    print("Error: need to specify model name")
    print("Usage: python your_script_name.py your.model")
    sys.exit(-1)

# 获取模型路径
model = sys.argv[1]

# 捕获 SIGINT 信号 (Ctrl+C)，以防程序在检测前或检测中途被用户手动停止
signal.signal(signal.SIGINT, signal_handler)

try:
    # 初始化检测器
    detector = snowboydecoder.HotwordDetector(model, sensitivity=0.5)
    print(f'Listening for model: {model}...')
    print('Press Ctrl+C to manually exit.')

    # main loop
    # 🚀 修改点 2: 将 detected_callback 更改为我们新的函数
    detector.start(detected_callback=detected_and_stop_callback,
                   interrupt_check=interrupt_callback,
                   sleep_time=0.03)

except Exception as e:
    print(f"程序运行出错: {e}")

finally:
    # 释放资源
    detector.terminate()
    print("✅ 检测器已关闭，程序退出。")

   
