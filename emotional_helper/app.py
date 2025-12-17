# encoding: utf-8
from __future__ import annotations

import base64
import json
import os
import random
import time
from pathlib import Path

import cv2
import pygame as py
import requests
import tkinter as tk
from PIL import ImageTk
from tkinter import Label, Message, StringVar

ROOT_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
MUSICLOGO_DIR = ASSETS_DIR / "musiclogo"
RUNTIME_DIR = ROOT_DIR / ".runtime"


def _env(name: str) -> str | None:
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else None


def _get_baidu_access_token(*, api_key: str, secret_key: str) -> str:
    token_url = "https://aip.baidubce.com/oauth/2.0/token"
    response = requests.get(
        token_url,
        params={
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": secret_key,
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Failed to get Baidu access_token: {payload}")
    return token


def baidu_tts_to_file(text: str, output_mp3: Path) -> None:
    api_key = _env("BAIDU_TTS_API_KEY")
    secret_key = _env("BAIDU_TTS_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError("Missing env: BAIDU_TTS_API_KEY / BAIDU_TTS_SECRET_KEY")

    token = _get_baidu_access_token(api_key=api_key, secret_key=secret_key)
    tts_url = "http://tsn.baidu.com/text2audio"
    response = requests.post(
        tts_url,
        data={"tok": token, "tex": text, "cuid": "EmotionalHelper", "lan": "zh", "ctp": 1},
        timeout=20,
    )
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "")
    if "audio/" not in content_type:
        raise RuntimeError(f"TTS failed: {response.text[:500]}")

    output_mp3.parent.mkdir(parents=True, exist_ok=True)
    output_mp3.write_bytes(response.content)


def detect_emotion_type_from_image(image_path: Path) -> str | None:
    api_key = _env("BAIDU_FACE_API_KEY")
    secret_key = _env("BAIDU_FACE_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError("Missing env: BAIDU_FACE_API_KEY / BAIDU_FACE_SECRET_KEY")

    token = _get_baidu_access_token(api_key=api_key, secret_key=secret_key)
    request_url = "https://aip.baidubce.com/rest/2.0/face/v3/detect"

    image_to_base64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    params = {
        "image": image_to_base64,
        "image_type": "BASE64",
        "face_field": "face_token,age,beauty,expression,emotion",
        "option": "COMMON",
    }

    response = requests.post(
        f"{request_url}?access_token={token}",
        data=params,
        headers={"content-type": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    result = response.json()
    if result.get("error_msg") != "SUCCESS":
        return None

    faces = (result.get("result") or {}).get("face_list") or []
    if not faces:
        return None
    emotion = (faces[0].get("emotion") or {}).get("type")
    return str(emotion) if emotion else None


def main() -> None:
    angryvoices = [
        "干什么那么生气？其实愤怒是双刃剑，人家是受伤，你自己也难受。为什么不平静下来呢？",
        "虽然你看起来在生气，但不带恶意。平静些，什么困难都可以解决的。",
        "生气可以，但你看到自己生气时的脸了吗？面目可憎！所以，不要生气，美才能回到你的脸上。",
        "啊，生气了，哈哈哈！你在生气，别人照样快乐。你吃亏了！",
        "啊哈，生气不好。生气有害于你的健康。保持不愠不怒，才有利于你的身体。长命百岁！",
    ]
    disgustvoices = [
        "这么讨厌人家？不要吧，人家也有长处。看到人家的长处，才有利于你的进步。",
        "呦呦呦，不要那么骄傲好不好？讨厌人家，你就那么完美？快乐点吧。",
        "有点讨厌？是的，看到社会人不文明不道德的行为，人人厌恶。我们要提倡社会公德。向你致敬！",
        "这些人在公共场所不检点不光是你，我也厌恶。讨厌！",
        "厌恶可以有，但不能常有。保持平和，对人对己都有利。",
    ]
    fearvoices = [
        "你看起来很不安。不要怕！事情并不是想象的那么坏，有时候等一等就会有转机。请保持冷静和智慧。",
        "怕了？不怕，有我呢！我们都在你身边，我们会保护你的。再说，警察也在不远处。",
        "怕？装的吧？你内心里并没有恐惧。看得出来，你在表演。",
        "怕是没有用的，任何时候，保持冷静的头脑，处事果断，一切困难和危险都可以解除的。",
        "你好像有点恐惧？我其实比你还紧张。没事，放宽心，一切都会好的。我就是这么鼓励自己的。",
    ]
    happyvoices = [
        "你看起来很高兴，真好！好的心情，所有事都会顺利。继续快乐！",
        "你好快乐啊！我也被你感染了，也快乐起来。我们就一起傻笑吧！",
        "你在笑，好！再多烦恼，一笑蓼之，有一首歌叫“笑比哭好”，让我们一起哈哈大笑吧。",
        "快乐的心情对健康特别有利，可以美颜常驻，可以神清气爽，可以长命百岁。",
        "你真诚的笑很美，我们都欣赏你，羡慕你。生活是多么美好啊！",
    ]
    sadvoices = [
        "怎么啦？心里难受吗？有什么委屈说出来，我们会帮助你的。",
        "感到伤心就哭出来，哭出来会好受很多。一切都会好的，要看到希望，看到未来。",
        "哭啦？为什么？这么伤心？不哭不哭不哭，好乖乖，笑一个。",
        "哦哟哟，好像挺伤心的，别装了！你挺会演戏啊，佩服你！",
        "不要伤心了，根本没事，你多心了。一切都好，你误会了。好了好了，笑一个！",
    ]
    surprisevoices = [
        "很惊讶？不要觉得惊奇，就是这么精彩！为多彩的生活点赞！",
        "你感到惊讶，好啊！后面想不到的惊喜还多着呢，会接踵而来，让你乐不可支。",
        "你显得很惊讶，觉得不可思议。这就是奇迹，世界很精彩！",
        "你的惊讶是装的。其实你很清楚这是什么。也好，逗个乐吧。",
        "你的惊讶的表情，显得你很单纯，甚至有些天真。很可爱啊！",
    ]
    neutralvoices = [
        "你的心情很平静，显示出你很有素养。心平气和，遇事不慌，这是有能力的表现。",
        "表面上你很平静，其实看得出来你想笑，装得有点不像。想笑就笑吧，不要这么绷着了，笑一个！",
        "平静的心情对健康有利，希望长期保持。",
        "看起来你没有什么表情，实际上你的内心波澜壮阔。胸有城府，含而不露，是个高人！",
        "你看起来平静，略带微笑，宽容，大度，睿智而有风度，是很受人尊敬的。",
    ]
    grimacevoices = [
        "做鬼脸，啊啊，我好害怕！不要吓我好不好？我胆小。",
        "不要做鬼脸，好难看啊！不信你照照镜子，把你的形象都破坏了。",
        "鬼脸真吓人！以后别做了好吗？",
        "你在做鬼脸，是不是你刚才做了什么坏事，不好意思了？请从实招来！",
        "看起来你在做鬼脸，但我觉得你心里在笑。够调皮的！",
    ]
    poutyvoices = [
        "你撅起了嘴，撅得挺高，可以挂一个瓶子了。",
        "你撅嘴了，有点不高兴？哈哈！挺有趣。",
        "撅嘴代表你不满意。那请你说说，怎么样才能使你满意？我们按你的做。",
        "撅起嘴嘴，好可爱啊！再坚持一会儿，我来拍个照。",
        "撅嘴了？生气了？不要那么多气，大家都很爱你的。和大家一块儿快乐吧。",
    ]

    volumes = 1.0
    py.mixer.init()
    py.mixer.music.set_volume(volumes)

    capture = cv2.VideoCapture(0)

    window = tk.Tk()
    window.title("情绪管理小帮手")
    window.geometry("310x200")
    window.minsize(310, 200)
    window.maxsize(310, 200)

    string = StringVar()
    musictextstr = StringVar()
    emotiontextstr = StringVar()
    entry_var1 = tk.StringVar()

    emo = tk.Label(window, textvariable=string, font=("微软雅黑", 12))
    musictext = tk.Label(window, textvariable=musictextstr, font=("微软雅黑", 12))
    emotiontext = Message(window, textvariable=emotiontextstr, width=300, font=("微软雅黑", 12))
    en2 = tk.Label(window, textvariable=entry_var1, justify=tk.CENTER)
    images = Label(window, width=85, height=85)

    image_angry = ImageTk.PhotoImage(file=str(MUSICLOGO_DIR / "angry.jpg"))
    image_disc = ImageTk.PhotoImage(file=str(MUSICLOGO_DIR / "disc.jpg"))
    image_sad = ImageTk.PhotoImage(file=str(MUSICLOGO_DIR / "sad.jpg"))
    image_fear = ImageTk.PhotoImage(file=str(MUSICLOGO_DIR / "fear.jpg"))
    image_disgust = ImageTk.PhotoImage(file=str(MUSICLOGO_DIR / "disgust.jpg"))
    image_happy = ImageTk.PhotoImage(file=str(MUSICLOGO_DIR / "happy.jpg"))

    emo.place(x=5, y=100)
    musictext.place(x=95, y=7.5)
    en2.place(x=95, y=35, width=130, height=15)
    emotiontext.place(x=1, y=125)

    finals = True
    total = True
    camerascan = True
    ifangrymusicplay = False
    ifdisgustmusicplay = False
    iffearmusicplay = False
    ifhappymusicplay = False
    ifsadmusicplay = False
    anymusicplay = False
    release = True
    musicpos = 0
    randoms = 0
    timeF = 5
    c = 1
    pause = True
    quits = 0

    string.set("您当前情绪为")
    images.config(image=image_disc)
    images.image = image_disc
    images.place(x=5, y=5)

    def inits() -> None:
        musictextstr.set("当前没有歌曲正在播放")
        images.config(image=image_disc)
        images.image = image_disc
        images.place(x=5, y=5)
        entry_var1.set("00:00")

    def stops() -> None:
        nonlocal pause
        py.mixer.music.pause()
        pause = True

    def starts() -> None:
        py.mixer.music.unpause()

    def ups() -> None:
        nonlocal volumes
        if volumes <= 1.0:
            volumes = round(volumes + 0.1, 1)
            py.mixer.music.set_volume(volumes)

    def downs() -> None:
        nonlocal volumes
        if volumes >= 0.0:
            volumes = round(volumes - 0.1, 1)
            py.mixer.music.set_volume(volumes)

    def times() -> None:
        musicposi = py.mixer.music.get_pos() / 1000 + musicpos / 1000
        seconds = int(musicposi if anymusicplay else py.mixer.music.get_pos() / 1000)
        entry_var1.set(f"{seconds//60:02d}:{seconds%60:02d}")

    def overs() -> None:
        nonlocal release, ifdisgustmusicplay, ifangrymusicplay, iffearmusicplay, ifsadmusicplay, ifhappymusicplay
        inits()
        py.mixer.music.stop()
        ifdisgustmusicplay = False
        ifangrymusicplay = False
        iffearmusicplay = False
        ifsadmusicplay = False
        ifhappymusicplay = False
        release = True

    def on_closing() -> None:
        nonlocal camerascan, total
        camerascan = False
        total = False
        window.destroy()
        py.mixer.music.stop()
        capture.release()

    def voiceplay(voice_path: Path) -> None:
        py.mixer.music.load(str(voice_path))
        py.mixer.music.play()

    tk.Button(window, text="暂停", width=1, height=1, command=stops).place(x=100, y=60)
    tk.Button(window, text="播放", width=1, height=1, command=starts).place(x=140, y=60)
    tk.Button(window, text="增大", width=1, height=1, command=ups).place(x=180, y=60)
    tk.Button(window, text="缩小", width=1, height=1, command=downs).place(x=220, y=60)
    tk.Button(window, text="释放", width=1, height=1, command=overs).place(x=260, y=60)

    inits()

    while True:
        anymusicplay = any([ifangrymusicplay, ifdisgustmusicplay, iffearmusicplay, ifhappymusicplay, ifsadmusicplay])
        if quits == 0:
            window.protocol("WM_DELETE_WINDOW", on_closing)
            quits = 1
        times()
        window.update()

        if camerascan:
            ref, frame = capture.read()
            if not ref:
                continue

        if c % timeF == 0 and camerascan and release:
            RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
            image_path = RUNTIME_DIR / "frame.jpg"
            cv2.imwrite(str(image_path), frame)

            try:
                emotion_type = detect_emotion_type_from_image(image_path)
            except Exception as e:
                emotion_type = None
                emotiontextstr.set(f"情绪识别失败：{e}")

            if not emotion_type:
                c += 1
                continue

            def _say(text: str) -> None:
                voice_path = RUNTIME_DIR / "voice.mp3"
                try:
                    baidu_tts_to_file(text, voice_path)
                    voiceplay(voice_path)
                except Exception as e:
                    emotiontextstr.set(f"{text}\n(语音合成失败：{e})")

            randoms = random.randint(0, 4)

            if emotion_type == "angry":
                string.set("您当前情绪为：生气")
                images.config(image=image_angry)
                images.image = image_angry
                musictextstr.set("致爱丽丝 - 贝多芬")
                emotiontextstr.set(angryvoices[randoms])
                _say(angryvoices[randoms])
                musicpos = py.mixer.music.get_pos()
                ifangrymusicplay = True
                release = False
            elif emotion_type == "disgust":
                string.set("您当前情绪为：讨厌")
                images.config(image=image_disgust)
                images.image = image_disgust
                musictextstr.set("River Flows In You - Yiruma")
                emotiontextstr.set(disgustvoices[randoms])
                _say(disgustvoices[randoms])
                musicpos = py.mixer.music.get_pos()
                ifdisgustmusicplay = True
                release = False
            elif emotion_type == "fear":
                string.set("您当前情绪为：恐惧")
                images.config(image=image_fear)
                images.image = image_fear
                musictextstr.set("未闻花名 - Oturans")
                emotiontextstr.set(fearvoices[randoms])
                _say(fearvoices[randoms])
                musicpos = py.mixer.music.get_pos()
                iffearmusicplay = True
                release = False
            elif emotion_type == "happy":
                string.set("您当前情绪为：开心")
                images.config(image=image_happy)
                images.image = image_happy
                musictextstr.set("LemonTree - Fool's Garden")
                emotiontextstr.set(happyvoices[randoms])
                _say(happyvoices[randoms])
                musicpos = py.mixer.music.get_pos()
                ifhappymusicplay = True
                release = False
            elif emotion_type == "sad":
                string.set("您当前情绪为：伤心")
                images.config(image=image_sad)
                images.image = image_sad
                musictextstr.set("欢乐颂 - 贝多芬")
                emotiontextstr.set(sadvoices[randoms])
                _say(sadvoices[randoms])
                musicpos = py.mixer.music.get_pos()
                ifsadmusicplay = True
                release = False
            elif emotion_type == "surprise":
                string.set("您当前情绪为：惊喜")
                emotiontextstr.set(surprisevoices[randoms])
                _say(surprisevoices[randoms])
                release = False
            elif emotion_type == "neutral":
                string.set("您当前情绪为：平静")
                emotiontextstr.set(neutralvoices[randoms])
                _say(neutralvoices[randoms])
                release = False
            elif emotion_type == "pouty":
                string.set("您当前情绪为：噘嘴")
                emotiontextstr.set(poutyvoices[randoms])
                _say(poutyvoices[randoms])
                release = False
            elif emotion_type == "grimace":
                string.set("您当前情绪为：鬼脸")
                emotiontextstr.set(grimacevoices[randoms])
                _say(grimacevoices[randoms])
                release = False

        c += 1

        if not py.mixer.music.get_busy() and ifangrymusicplay:
            py.mixer.music.load(str(MUSIC_DIR / "angry.mp3"))
            py.mixer.music.play(start=musicpos / 1000)
        elif not py.mixer.music.get_busy() and ifdisgustmusicplay:
            py.mixer.music.load(str(MUSIC_DIR / "disgust.mp3"))
            py.mixer.music.play(start=musicpos / 1000)
        elif not py.mixer.music.get_busy() and iffearmusicplay:
            py.mixer.music.load(str(MUSIC_DIR / "fear.mp3"))
            py.mixer.music.play(start=musicpos / 1000)
        elif not py.mixer.music.get_busy() and ifhappymusicplay:
            py.mixer.music.load(str(MUSIC_DIR / "happy.mp3"))
            py.mixer.music.play(start=musicpos / 1000)
        elif not py.mixer.music.get_busy() and ifsadmusicplay:
            py.mixer.music.load(str(MUSIC_DIR / "sad.mp3"))
            py.mixer.music.play(start=musicpos / 1000)

        time.sleep(0.01)


if __name__ == "__main__":
    main()

