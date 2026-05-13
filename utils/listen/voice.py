#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import websocket
import datetime
import hashlib
import base64
import hmac
import json
import os
import time
import ssl
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from time import mktime
import _thread as thread
import sounddevice as sd
import soundfile as sf
import numpy as np

from dotenv import load_dotenv

# 加载 .env 文件中的环境变量，注意修改根目录的环境变量
load_dotenv()

class Voice:
    def __init__(self, duration=5,app_id = os.getenv("VOICE_APP_ID"),
        api_secret = os.getenv("VOICE_API_SECRET"),
        api_key = os.getenv("VOICE_API_KEY")):
        # 读取环境变量
        self.app_id=app_id
        self.api_secret=api_secret
        self.api_key=api_key
        self.audio_file = 'output.wav'
        self.duration = duration  # 恢复 duration 参数
        self.full_text = []
        self.ws = None

    def record(self):
        """录音方法"""
        print(f"🎤 正在录音 ({self.duration}秒)... 请说话")
        # 录制
        recording = sd.rec(int(self.duration * 16000), 
                         samplerate=16000, 
                         channels=1, 
                         dtype='int16')
        sd.wait()
        # 保存
        sf.write(self.audio_file, recording, 16000)
        
        # 简单检查音量，防止麦克风没声音
        volume = np.max(np.abs(recording))
        if volume < 500:
            print(f"⚠️ 警告：录音音量极低 ({volume})，请检查麦克风设置")
        else:
            print("✅ 录音完成")

    def create_url(self):
        url = 'wss://iat-api.xfyun.cn/v2/iat'
        host = 'iat-api.xfyun.cn'
        now = datetime.datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.api_key, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        v = {
            "authorization": authorization,
            "date": date,
            "host": host
        }
        return url + '?' + urlencode(v)

    def on_open(self, ws):
        def run(*args):
            frameSize = 1280 
            intervel = 0.04 
            status = 0 

            # 使用 soundfile 直接读取数据，避免文件头噪音
            try:
                data, fs = sf.read(self.audio_file, dtype='int16')
                audio_bytes = data.tobytes()
            except Exception as e:
                print(f"读取音频出错: {e}")
                ws.close()
                return

            offset = 0
            while True:
                if offset >= len(audio_bytes):
                    status = 2
                    buf = b"" 
                else:
                    end = offset + frameSize
                    buf = audio_bytes[offset:end]
                    if len(buf) < frameSize:
                        status = 2
                
                # 发送第一帧
                if status == 0:
                    d = {
                        "common": {"app_id": self.app_id},
                        "business": {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo":1, "vad_eos":10000},
                        "data": {"status": 0, "format": "audio/L16;rate=16000",
                                 "audio": str(base64.b64encode(buf), 'utf-8'),
                                 "encoding": "raw"}
                    }
                    ws.send(json.dumps(d))
                    status = 1
                
                # 发送中间帧
                elif status == 1:
                    d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                    if not buf: status = 2
                
                # 发送最后一帧
                elif status == 2:
                    d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                    break
                
                offset += frameSize
                time.sleep(intervel)

        thread.start_new_thread(run, ())

    def on_message(self, ws, message):
        try:
            msg = json.loads(message)
            if msg["code"] != 0:
                print(f"API Error: {msg['message']}")
                ws.close()
            else:
                data = msg["data"]["result"]["ws"]
                text = "".join([w["w"] for i in data for w in i["cw"]])
                if text:
                    self.full_text.append(text)
                
                # 收到结束标志
                if msg["data"]["status"] == 2:
                    ws.close()
        except Exception as e:
            print(f"解析错误: {e}")

    def on_error(self, ws, error):
        print(f"连接错误: {error}")

    def on_close(self, ws, *args):
        pass

    def recognize(self):
        self.full_text = [] # 清空上次结果
        websocket.enableTrace(False) # 关闭调试刷屏
        wsUrl = self.create_url()
        self.ws = websocket.WebSocketApp(
            wsUrl,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        return "".join(self.full_text)

# 简单的自测代码
if __name__ == '__main__':
    v = Voice(duration=3)
    v.record()
    print(v.recognize())