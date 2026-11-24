import os
import json
import math
import random
import subprocess
from collections import defaultdict, deque
from pathlib import Path
from datetime import datetime, date, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

JST = timezone(timedelta(hours=9))
today = datetime.now(JST).date()
slot = int(os.environ.get("VIDEO_SLOT", "0"))

if slot not in (0, 1, 2):
    raise ValueError("Invalid VIDEO_SLOT")

questions = json.loads(
    Path("questions.json").read_text(encoding="utf-8")
)

if not questions:
    raise ValueError("Question bank is empty")

# Validate all questions
seen = set()

for item in questions:
    if len(item["choices"]) != 4:
        raise ValueError("Invalid choices")
    if len(item["explanations"]) != 3:
        raise ValueError("Invalid explanations")
    if not 0 <= int(item["correct_index"]) < 4:
        raise ValueError("Invalid correct_index")
    key = item["question"].strip()
    if key in seen:
        raise ValueError("Duplicate question: " + key)
    seen.add(key)

# Mix categories without repeating questions
rng = random.Random(20261124)
groups = defaultdict(list)

for item in questions:
    groups[item["category"]].append(item)

for category in groups:
    rng.shuffle(groups[category])

groups = {
    category: deque(items)
    for category, items in groups.items()
}

mixed = []
previous = None

while any(groups.values()):
    available = [
        category for category in groups
        if groups[category] and category != previous
    ]

    if not available:
        available = [
            category for category in groups
            if groups[category]
        ]

    category = max(
        available,
        key=lambda c: len(groups[c])
    )

    mixed.append(groups[category].popleft())
    previous = category

start_date = date(2026, 11, 24)
day_index = (today - start_date).days
index = (day_index * 3 + slot) % len(mixed)

q = mixed[index]

# Shuffle answer positions deterministically
answer = q["choices"][int(q["correct_index"])]
order = list(range(4))

answer_rng = random.Random(20261124 + index)
answer_rng.shuffle(order)

choices = [q["choices"][i] for i in order]
correct_index = order.index(int(q["correct_index"]))
explanations = q["explanations"]

os.makedirs("output", exist_ok=True)

title = (
    f"{q['category']} Challenge: "
    f"{q['question']} #Shorts"
)

if len(title) > 100:
    title = title[:89].rstrip() + "... #Shorts"

metadata = {
    "title": title,
    "description": (
        f"Try this {q['category']} puzzle!\n"
        "Watch for the answer and explanation.\n"
        "Comment how fast you solved it!\n"
        "#BrainTeaser #Quiz #Shorts"
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
        fonts[size] = ImageFont.truetype(
            font_path, size
        )
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

def wrap_text(draw, text, size, max_width):
    lines = []
    line = ""

    for word in str(text).split():
        candidate = (
            line + " " + word if line else word
        )

        if (
            draw.textlength(
                candidate, font=font(size)
            ) > max_width and line
        ):
            lines.append(line)
            line = word
        else:
            line = candidate

    if line:
        lines.append(line)

    return lines

def text_block(draw, text, y, size,
               max_width, max_height,
               color="white"):

    while size > 14:
        lines = wrap_text(
            draw, text, size, max_width
        )

        line_height = size + 8

        if len(lines) * line_height <= max_height:
            break

        size -= 2

    lines = wrap_text(
        draw, text, size, max_width
    )

    line_height = size + 8
    top = y - len(lines) * line_height // 2

    for line in lines:
        center(
            draw, line, top, size,
            color, max_width
        )
        top += line_height

def rounded(draw, xy, fill,
            outline=None, width=2, radius=20):

    draw.rounded_rectangle(
        xy, radius=radius, fill=fill,
        outline=outline, width=width
    )

# Different colors for each category
palettes = [
    ("#20132F", "#C69CFF"),
    ("#0B1430", "#6BDFFF"),
    ("#10291F", "#75FFBB"),
    ("#301A35", "#FFA8EE"),
    ("#302313", "#FFD166"),
    ("#302020", "#FF9999"),
    ("#102C32", "#71E8E8")
]

categories = sorted({
    item["category"] for item in questions
})

category_index = categories.index(q["category"])

base, accent = palettes[
    category_index % len(palettes)
]

background = Image.new("RGB", (W, H), base)
bd = ImageDraw.Draw(background)

rgb = tuple(
    int(base[i:i+2], 16) for i in (1, 3, 5)
)

for y in range(H):
    glow = int(
        22 * (1 + math.sin(y / 180)) / 2
    )

    bd.line(
        (0, y, W, y),
        fill=tuple(
            min(255, c + glow) for c in rgb
        )
    )

def make_frame(t):
    img = background.copy()
    d = ImageDraw.Draw(img)

    for i in range(30):
        x = (i * 193 + 37) % W
        y = int((i * 257 + 71 - t * 13) % H)
        r = 2 + i % 3

        d.ellipse(
            (x-r, y-r, x+r, y+r),
            fill="#3465A0"
        )

    d.rounded_rectangle(
        (25, 45, 695, 1230),
        radius=35,
        outline=accent,
        width=4
    )

    center(
        d, "PICO BRAIN CHALLENGE",
        80, 30, accent
    )

    center(
        d, "DAILY MIND PUZZLES",
        135, 34, "#FFD166"
    )

    rounded(
        d, (110, 212, 610, 270),
        "#20385E", accent
    )

    center(
        d,
        f"{q['category']} / {q['difficulty']}",
        220, 30,
        max_width=470
    )

    center(d, q["heading"], 315, 44)

    # Multiline question display
    rounded(
        d, (55, 405, 665, 585),
        "#172D50", accent, 4
    )

    text_block(
        d, q["question"],
        495, 42, 555, 160
    )

    # Answer choices
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
            label,
            font=font(size),
            fill="white"
        )

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
                d,
                (90, 1010, 90+width, 1030),
                accent,
                radius=8
            )

        center(
            d, "Think carefully!",
            1080, 30
        )

    elif t < 20:
        center(
            d,
            f"Correct: {'ABCD'[correct_index]}!",
            915, 52, "#66FFB8"
        )

        center(
            d, f"Answer: {answer}",
            1015, 36, "#FFD166"
        )

    elif t < 28:
        center(
            d, "Here is why",
            870, 35, "#FFD166"
        )

        phase = min(
            3, max(1, int((t-20)/2.3)+1)
        )

        for i in range(phase):
            text_block(
                d,
                explanations[i],
                950 + i*80,
                30,
                580,
                75,
                "#80E8FF"
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

    rounded(
        d, (60, 1185, 660, 1195),
        "#334566", radius=4
    )

    progress = int(600*t/DURATION)

    if progress > 0:
        rounded(
            d,
            (60, 1185, 60+progress, 1195),
            "#FFD166",
            radius=4
        )

    return img

cmd = [
    "ffmpeg", "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}",
    "-r", str(FPS),
    "-i", "-",
    "-f", "lavfi",
    "-i",
    "sine=frequency=440:sample_rate=44100",
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
    raise RuntimeError("Video generation failed")

print("Video generated successfully")
print("Question ID:", q["id"])
print("Category:", q["category"])
print("Answer:", answer)
print("Title:", title)
