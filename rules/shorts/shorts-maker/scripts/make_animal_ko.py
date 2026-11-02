import os, subprocess, json
from PIL import Image, ImageDraw, ImageFont

ROOT = "/tmp/claude-0/-home-user-studiolani/8a967740-042e-59aa-a31c-9e7d099e521e/scratchpad"
V = f"{ROOT}/vids"
F = f"{ROOT}/fonts"
OUT = f"{ROOT}/build"
os.makedirs(f"{OUT}/png", exist_ok=True); os.makedirs(f"{OUT}/seg", exist_ok=True)

W, H = 1080, 1920
TOP, BOT = 516, 0
BX, BW, BH = 52, 976, 1019   # 템플릿 투명 칸
VH = H - TOP - BOT             # 1134
TITLE_FONT = f"{F}/BMDOHYEON.ttf"   # 배민 도현 (대표님 지정, 제목 105)
NAR_FONT = f"{F}/narration.ttf"   # 해설 (대표님 지정)
MIND_FONT = f"{F}/HSHwalkong.ttf"   # 강아지 2번 속마음 (노랑 글씨+검정 상자)
DOG_FONT = f"{F}/GriunYeeun-Rg.ttf"   # 그리운 예은 (대표님 지정, 강아지 1번·사람 대사)
WHITE, YELLOW, MINT = "#FFFFFF", "#FFE006", "#8CE99A"

TITLE = ["눈나가 간식 꺼냈더니.."]

def text_png(path, text, font_path, size, color, stroke=10, spacing=0, skew=0.0):
    font = ImageFont.truetype(font_path, size)
    img0 = Image.new("RGBA", (W*2, 400), (0,0,0,0)); d0 = ImageDraw.Draw(img0)
    # 글자별로 그려서 자간 적용
    x = 40; parts=[]
    for ch in text:
        bb = d0.textbbox((0,0), ch, font=font, stroke_width=stroke)
        adv = font.getlength(ch)
        parts.append((x, ch)); x += adv + spacing
    for px,ch in parts:
        d0.text((px, 40), ch, font=font, fill=color, stroke_width=stroke, stroke_fill="black")
    bbox = img0.getbbox(); img = img0.crop(bbox)
    if skew:
        w,h = img.size; pad=int(h*abs(skew))+2
        canvas = Image.new("RGBA",(w+pad*2,h),(0,0,0,0)); canvas.paste(img,(pad,0))
        img = canvas.transform(canvas.size, Image.AFFINE, (1, skew, -skew*h/2 if skew>0 else 0, 0, 1, 0), resample=Image.BICUBIC)
        img = img.crop(img.getbbox())
    img.save(path); return img.size

def mind_png(path, text, color="#FFE006"):  # 속마음·효과 노랑 FFE006 (대표님 확정)
    font = ImageFont.truetype(MIND_FONT, 64)
    d0 = ImageDraw.Draw(Image.new("RGBA",(10,10)))
    x0,y0,x1,y1 = d0.textbbox((0,0), text, font=font); tw,th = x1-x0, y1-y0
    px,py = 30,24
    img = Image.new("RGBA", (tw+px*2, th+py*2), (0,0,0,255)); d = ImageDraw.Draw(img)
    d.text((px-x0, py-y0), text, font=font, fill=color, stroke_width=1, stroke_fill=color)
    img.save(path); return img.size

# 제목 PNG (위 검정 띠 가운데, 2줄, 흰+노랑)
def title_png(path):
    tw,th = text_png(path+".tmp.png", TITLE[0], TITLE_FONT, 66, "#111111", 1, spacing=0, skew=0.22)
    t = Image.open(path+".tmp.png")
    img = Image.new("RGBA", (W, TOP), (0,0,0,0)); img.paste(t, ((W-tw)//2, 455-th//2), t); img.save(path)

# 장면: (원본, 시작, 끝, 세로 자르기 y(1920 기준), 원본소리, 자막들[(시작,끝,텍스트,화자)])
SCENES = [
    ("v3", 0.0, 2.4, 520, False, [(0.0,1.2,"눈나가 간식을","n"),(1.2,2.4,"꺼냈는데","n")]),
    ("v3", 3.0, 5.0, 520, False, [(0.2,2.0,"눈나 그거 뭐야","d")]),
    ("v3", 8.3, 10.2, 350, True,  [(0.0,0.7,"*덥석*","m"),(0.7,1.9,"내 거!","d")]),
    ("v1", 0.8, 3.0, 358, False, [(0.0,1.0,"못 받자 코만","n"),(1.0,2.2,"계속 핥았다네요","n")]),
    ("v1", 4.8, 6.6, 358, False, [(0.2,1.8,"눈나 한 입만","d")]),
    ("v1", 7.3, 8.1, 358, False, [(0.0,0.8,"핥으면 나오는 줄","n")]),
    ("v1", 9.0, 9.7, 358, False, [(0.0,0.7,"알았는지..","n")]),
    ("v1", 10.4, 11.0, 358, False,[(0.0,0.6,"알았는지..","n")]),
    ("v1", 11.4, 12.4, 358, False,[(0.0,1.0,"눈나아..","d")]),
    ("v2", 0.0, 2.2, 358, False, [(0.0,1.0,"코가 다 닳도록","n"),(1.0,2.2,"핥았는데","n")]),
    ("v2", 2.2, 4.8, 358, False, [(0.2,2.6,"눈나 안 줄 거야?","d")]),
]
NAR_Y = 1594   # 영상 칸 아래 흰 바탕 (블로 화면 기준)   # 해설 자막 중심
DOG_Y = 1384   # 대사: 영상 칸 안 아래쪽 (대표님 화면 실측)
MIND_Y = 1388  # 속마음 상자 세로 중심 (대표님 화면 실측)    # 강아지 자막(머리 위쪽)

title_png(f"{OUT}/png/title.png")
segs = []
for i,(src,s,e,cy,keep_audio,caps) in enumerate(SCENES):
    dur = round(e-s,3)
    inputs = ["-ss",str(s),"-t",str(dur),"-i",f"{V}/{src}.mp4","-i",f"{OUT}/png/title.png","-i",f"{OUT}/template_mnhanip.png"]
    fc = f"color=white:s={W}x{H}:r=30:d={dur}[base];[0:v]scale={BW}:-2,crop={BW}:{BH}:0:{cy}[vid];[base][vid]overlay={BX}:{TOP}[v00];[2:v]scale={W}:{H}[tpl];[v00][tpl]overlay=0:0[v0];[v0][1:v]overlay=0:0[v1]"
    last="v1"; n=3
    for j,(cs,ce,txt,who) in enumerate(caps):
        p=f"{OUT}/png/c{i}_{j}.png"
        if who=="n": tw,th = text_png(p, txt, NAR_FONT, 72, "#111111", 2, spacing=-3); y=NAR_Y
        elif who=="m": tw,th = mind_png(p, txt); y=MIND_Y
        else:        tw,th = text_png(p, txt, DOG_FONT, 74, WHITE, 10);  y=DOG_Y
        inputs += ["-i",p]
        fc += f";[{last}][{n}:v]overlay=(W-w)/2:{y - th//2}:enable='gte(t,{cs})*lt(t,{ce})'[v{n}]"
        last=f"v{n}"; n+=1
    if keep_audio:
        afc = ";[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=6dB[a]"
    else:
        inputs += ["-f","lavfi","-t",str(dur),"-i","anullsrc=r=48000:cl=stereo"]
        afc = f";[{n}:a]anull[a]"
    out=f"{OUT}/seg/s{i:02d}.mp4"
    cmd=["ffmpeg","-v","error","-y"]+inputs+["-filter_complex",fc+afc,"-map",f"[{last}]","-map","[a]",
         "-r","30","-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",out]
    subprocess.run(cmd,check=True); segs.append(out)

with open(f"{OUT}/list.txt","w") as f:
    for sgm in segs: f.write(f"file '{sgm}'\n")
subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",f"{OUT}/list.txt",
                "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-r","30",
                "-af","loudnorm=I=-10:TP=-1.5:LRA=7","-c:a","aac","-b:a","192k",f"{OUT}/final_v18.mp4"],check=True)
print("done")
