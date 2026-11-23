
import os
import json
import math
import random
import subprocess
from pathlib import Path
from datetime import datetime, date, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

# 日本時間と投稿枠
JST = timezone(timedelta(hours=9))
today = datetime.now(JST).date()
slot = int(os.environ.get("VIDEO_SLOT", "0"))

if slot not in (0, 1, 2):
    raise ValueError("VIDEO_SLOTは0、1、2のみ")

# 100 questionsを順番に使用
questions = json.loads(
    Path("questions.json").read_text(encoding="utf-8")
)
if len(questions) != 100:
    raise ValueError("問題数が100 questionsではありません")

start_date = date(2026, 11, 24)
day_index = (today - start_date).days
index = (day_index * 3 + slot) % len(questions)
q = questions[index]

choices = q["choices"]
correct_index = int(q["correct_index"])
answer = choices[correct_index]
explanations = q["explanations"]

if len(choices) != 4 or len(explanations) != 3:
    raise ValueError("問題データの形式が不正です")
if not 0 <= correct_index < 4:
    raise ValueError("正解番号が不正です")

# タイトルも自動生成
os.makedirs("output", exist_ok=True)

title = (
    f"{q['difficulty']}: "
    f"{q['category']} Quiz! "
    f"Can you solve it? #Shorts"
)

metadata = {
    "title": title,
    "description": (
        f"Try this {q['category']} puzzle!\n"
        "Watch for the answer and explanation.\n"
        "Comment how fast you solved it!\n"
        "#BrainTeaser #MathQuiz #Shorts"
    )
}

Path("output/metadata.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

W, H = 720, 1280
FPS = 10
DURATION = 30

font_path = (
    "/usr/share/fonts/opentype/noto/"
    "NotoSansCJK-Regular.ttc"
)
fonts = {}

def font(size):
    if size not in fonts:
        fonts[size] = ImageFont.truetype(font_path, size)
    return fonts[size]

def fit_size(draw, text, size, max_width):
    while size > 17:
        bounds = draw.textbbox(
            (0, 0), str(text), font=font(size)
        )
        if bounds[2] - bounds[0] <= max_width:
            break
        size -= 2
    return size

def center(draw, text, y, size=36,
           color="white", max_width=600):
    size = fit_size(draw, text, size, max_width)
    draw.text(
        (W // 2, y), str(text),
        font=font(size),
        fill=color, anchor="mt"
    )

def rounded(draw, xy, fill,
            outline=None, width=2, radius=20):
    draw.rounded_rectangle(
        xy, radius=radius, fill=fill,
        outline=outline, width=width
    )

# ネオン背景
background = Image.new("RGB", (W, H), "#20132F")
bd = ImageDraw.Draw(background)

for y in range(H):
    glow = int(22 * (1 + math.sin(y / 180)) / 2)
    bd.line(
        (0, y, W, y),
        fill=(35 + glow // 2,
              12 + glow // 2, 48 + glow)
    )

def make_frame(t):
    img = background.copy()
    d = ImageDraw.Draw(img)

    # 動く光の粒
    for i in range(30):
        x = (i * 193 + 37) % W
        y = int((i * 257 + 71 - t * 13) % H)
        r = 2 + i % 3
        d.ellipse(
            (x-r, y-r, x+r, y+r),
            fill="#3465A0"
        )

    # 光る外枠
    pulse = int(20 * math.sin(t * 2))
    border = (175, 100 + pulse, 245)
    d.rounded_rectangle(
        (25, 45, 695, 1230),
        radius=35, outline=border, width=4
    )

    center(d, "PICO BRAIN CHALLENGE",
           80, 30, "#6BDFFF")
    center(d, "DAILY MIND PUZZLES",
           135, 34, "#FFD166")

    rounded(
        d, (215, 212, 505, 270),
        "#20385E", "#6BDFFF"
    )
    center(
        d,
        f"{q['category']} / {q['difficulty']}",
        220, 30
    )

    center(d, q["heading"], 315, 44)

    # 問題表示
    rounded(
        d, (55, 425, 665, 565),
        "#172D50", "#3FD8FF", 4
    )
    center(
        d, q["question"], 467, 42,
        max_width=565
    )

    # 4択
    for i, value in enumerate(choices):
        x = 65 + (i % 2) * 305
        y = 615 + (i // 2) * 115

        revealed = t >= 17
        is_correct = i == correct_index

        bg = (
            "#146A50"
            if revealed and is_correct
            else "#1D3156"
        )
        edge = (
            "#52FFB8"
            if revealed and is_correct
            else "#496B9D"
        )

        rounded(
            d, (x, y, x+285, y+85),
            bg, edge, 3
        )

        label = f"{'ABCD'[i]}: {value}"
        size = fit_size(d, label, 34, 255)
        d.text(
            (x+15, y+22),
            label, font=font(size),
            fill="white"
        )

    # 時間に合わせた演出
    if t < 4:
        center(
            d, "Can you solve it?",
            910, 47, "#FFD166"
        )
        center(
            d, "Pick your answer!",
            1005, 30
        )

    elif t < 17:
        remain = math.ceil(17-t)
        center(
            d, f"{remain} seconds left",
            910, 48, "#FFD166"
        )

        rounded(
            d, (90, 1010, 630, 1030),
            "#31466A"
        )
        width = int(
            540 * max(0, (17-t)/13)
        )
        if width > 0:
            rounded(
                d, (90, 1010, 90+width, 1030),
                "#4DE0FF", radius=8
            )

        center(
            d, "Think carefully!",
            1080, 30
        )

    elif t < 20:
        center(
            d, f"Correct: {'ABCD'[correct_index]}！",
            915, 52, "#66FFB8"
        )
        center(
            d, f"Answer: {answer}",
            1015, 36, "#FFD166"
        )

    elif t < 28:
        center(
            d, "Here is why",
            890, 35, "#FFD166"
        )

        phase = min(
            3, max(1, int((t-20)/2.3)+1)
        )

        for i in range(phase):
            center(
                d, explanations[i],
                960 + i*65,
                31, "#80E8FF"
            )

    else:
        center(
            d, f"Answer: {answer}",
            920, 43, "#66FFB8"
        )
        center(
            d, "Did you get it? Comment!",
            1040, 29, "#FFD166"
        )

    # 進行ゲージ
    rounded(
        d, (60, 1185, 660, 1195),
        "#334566", radius=4
    )
    progress = int(600*t/DURATION)
    if progress > 0:
        rounded(
            d, (60, 1185, 60+progress, 1195),
            "#FFD166", radius=4
        )

    return img

# 動画と仮音声を生成
cmd = [
    "ffmpeg", "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}",
    "-r", str(FPS),
    "-i", "-",
    "-f", "lavfi",
    "-i", "sine=frequency=440:sample_rate=44100",
    "-filter_complex",
    "[1:a]volume=0.015,atrim=duration=30[a]",
    "-map", "0:v",
    "-map", "[a]",
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "96k",
    "-movflags", "+faststart",
    "-t", str(DURATION),
    "output/short.mp4"
]

proc = subprocess.Popen(
    cmd, stdin=subprocess.PIPE
)

try:
    for n in range(DURATION*FPS):
        frame = make_frame(n/FPS)
        proc.stdin.write(frame.tobytes())
finally:
    proc.stdin.close()

if proc.wait() != 0:
    raise RuntimeError("動画生成に失敗しました")

print("動画生成成功")
print("問題番号:", index+1)
print("ジャンル:", q["category"])
print("正解:", answer)
print("タイトル:", title)
