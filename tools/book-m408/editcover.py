from PIL import Image, ImageDraw, ImageFont
im=Image.open('cover-orig.jpg').convert('RGB')
d=ImageDraw.Draw(im)
BG=(19,33,60); CREAM=(236,234,222); GOLD=(201,168,87)
d.rectangle((76,1122,700,1172),fill=BG)
SC=2  # 'Noto Serif CJK SC' index 2 in ttc? find by name
def font(path,size):
    for i in range(10):
        f=ImageFont.truetype(path,size,index=i)
        if 'SC' in f.getname()[0]: return f
F=font('/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc',34)
F2=font('/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc',24)
# letter-spaced like original: 王 德 生   著  (x 82..271)
def spaced(x,y,txt,f,gap,fill):
    for ch in txt:
        if ch==' ': x+=gap; continue
        d.text((x,y),ch,font=f,fill=fill); x+=f.getlength(ch)+gap
    return x
x=spaced(82,1126,'陈晓艳',F,6,CREAM)
x=spaced(x+26,1126,'著',F,0,CREAM)
x=spaced(x+46,1134,'王德生',F2,4,(190,196,206))
spaced(x+14,1134,'指导',F2,2,(190,196,206))
im.save('cover.jpg',quality=92)
im.crop((60,1080,800,1200)).save('crop_new.png')
