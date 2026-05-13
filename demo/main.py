#!/bin/python3
# 直接 唤醒 并且执行某个函数
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils/wakeUp'))
import snowboydecoder
import sys
import signal
import os
import mission
# 执行 bash 类
# pip3 install subprocess 

class Rundev():
    def __init__(self,model,sensitivity=0.5,sleep_time=0.03):
        # 外置参数
        self.model = model
        self.sensitivity = sensitivity
        self.sleep_time = sleep_time
        self.detector = None
        #内置参数 
        self.interrupted = False
        #self.greeting = os.path.join(os.path.dirname(__file__), '..', 'config/wavDir/greeting.wav')
        self.mission = mission.Mission()

    def interrupt_callback(self):
        return self.interrupted
    def signal_handler(self,signal, frame):
        self.interrupted = True  

    #  回调函数，语音识别在这里实现
    def callbacks(self):

        # 语音唤醒后，提示ding两声
        snowboydecoder.play_audio_file()
        # snowboydecoder.play_audio_file()

        #  关闭snowboy功能
        self.detector.terminate()
        
        self.mission.run()#整个agent的接入点
        
        # 打开snowboy功能
        self.run()    # wake_up —> monitor —> wake_up  递归调用

    def run(self):
        print('正在监听中.........','按 Ctrl+C 停止运行')

        # capture SIGINT signal, e.g., Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)

        self.detector = snowboydecoder.HotwordDetector(
            self.model, 
            sensitivity =self.sensitivity)

        # main loop
        self.detector.start(detected_callback=self.callbacks,
               interrupt_check=self.interrupt_callback,
               sleep_time=self.sleep_time)
        # 使终止
        self.detector.terminate()
        


# 测试
if __name__ == "__main__":
    dev = Rundev(os.path.join(os.path.dirname(__file__), '..', 'utils/wakeUp/xiaodu.pmdl'))
    dev.run()


