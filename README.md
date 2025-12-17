# EmotionalHelper（情绪管理小帮手）

一个基于摄像头的人脸情绪识别 + 音乐/语音安抚的小工具（Tkinter + OpenCV + Pygame），情绪识别与语音合成使用百度智能云接口。

## 目录结构

- `emotional_helper/app.py`：主程序入口
- `assets/music/`：情绪对应的背景音乐
- `assets/musiclogo/`：界面图标
- `assets/logo.ico`：图标资源

## 运行

1. 安装依赖
   - `python3 -m venv .venv && source .venv/bin/activate`
   - `pip install -r requirements.txt`
2. 配置环境变量（需要你自己的百度接口 Key）
   - `export BAIDU_FACE_API_KEY=...`
   - `export BAIDU_FACE_SECRET_KEY=...`
   - `export BAIDU_TTS_API_KEY=...`
   - `export BAIDU_TTS_SECRET_KEY=...`
3. 启动
   - `python -m emotional_helper.app`

## 说明

- 程序会在 `EmotionalHelper/.runtime/` 下生成临时文件（截图帧、语音 mp3），已加入 `.gitignore`。

# EmotionalHelper
