import base64,re,sys
M='maker-assets'; b=lambda p: base64.b64encode(open(p,'rb').read()).decode()
src=open('maker_src.html',encoding='utf-8').read()
for k,f in [('FONT_BM','fonts/BMDOHYEON.woff2'),('FONT_NARR','fonts/KoreanCNMM-narration.woff2'),('FONT_GRIUN','fonts/GriunYeeun-Rg.woff2'),('FONT_HS','fonts/HSHwalkongSerif-Regular.woff2'),('FONT_MPLUS','fonts/MPLUSRounded1c-Black.woff2'),('FONT_PL','fonts/Paperlogy-7Bold.woff2'),('TEMPLATE_PNG','template.png')]:
    src=src.replace('{{'+k+'}}',b(f'{M}/{f}'))
open('쇼츠제작실.html','w',encoding='utf-8').write(src)
# artifact variant: no doctype/html/head/body
head=src.split('<head>')[1].split('</head>')[0]; body=src.split('<body>')[1].rsplit('</body>')[0]
title=re.search(r'<title>.*?</title>',head).group(0); style=head[head.index('<style>'):head.index('</style>')+8]
art=title+'\n<meta name="claude:viewport-fit-sides" content="cover">\n'+style+'\n'+body
open('artifact.html','w',encoding='utf-8').write(art)
print('built', len(src), len(art))
