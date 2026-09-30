import copy, re, subprocess
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from v4lib import *
from v4lib import _tblpr, _grid, _cell

GRAY_BORDER = 'C9D6CC'
SRC = '/home/claude/환경아카이브_풀숲_통합_임팩트_측정_보고서_v0_4.docx'
OUT = '/home/claude/환경아카이브_풀숲_통합_임팩트_측정_보고서_v0_9.docx'
doc = Document(SRC)
body_el = doc.element.body

def replace_in_para(p, old, new):
    txt = ptext(p)
    if old not in txt: return False
    first_rpr = None
    for r in p.iter(qn('w:r')):
        rp = r.find(qn('w:rPr'))
        if rp is not None: first_rpr = copy.deepcopy(rp)
        break
    new_txt = txt.replace(old, new)
    for ch in list(p):
        if ch.tag != qn('w:pPr'): p.remove(ch)
    r = mk(f'<w:r><w:t xml:space="preserve">{esc(new_txt)}</w:t></w:r>')
    if first_rpr is not None: r.insert(0, first_rpr)
    p.append(r)
    return True

def find_para(startswith=None, contains=None):
    for p in body_el.iter(qn('w:p')):
        t = ptext(p)
        if startswith and t.startswith(startswith): return p
        if contains and contains in t: return p
    return None

def kids(): return list(body_el)

# ---------------------------------------------------------------
# 3·4. 문구 삭제
# ---------------------------------------------------------------
p = find_para(contains="(2026.8 Omeka DB 기준 '기록-작품사진' 유형 9,183점·작가 정보사전 60건 등록),")
replace_in_para(p, "아카이빙하였으며(2026.8 Omeka DB 기준 '기록-작품사진' 유형 9,183점·작가 정보사전 60건 등록), ", "아카이빙하였으며, ")
p = find_para(contains='국가기록원조차 환경사진을 별도로 아카이빙하지 않는 상황에서, ')
replace_in_para(p, '국가기록원조차 환경사진을 별도로 아카이빙하지 않는 상황에서, 환경사진아카이브는', '환경사진아카이브는')

# ---------------------------------------------------------------
# 5·6. 3.5절 재구성 (연계 개념도 + 발췌 박스)
# ---------------------------------------------------------------
K = kids()
i35 = next(i for i, k in enumerate(K) if ptext(k).startswith('3.5 풀숲과의 연계'))
i36 = next(i for i, k in enumerate(K) if ptext(k).startswith('3.6 사진예술계'))
# 재사용 이미지 run
old = K[i35:i36]
img_lee = img_kim = img_doc = None
for el in old:
    for r in el.iter(qn('w:r')):
        if r.find(qn('w:drawing')) is not None:
            cap = ''
            if img_lee is None: img_lee = copy.deepcopy(r)
            elif img_kim is None: img_kim = copy.deepcopy(r)
            elif img_doc is None: img_doc = copy.deepcopy(r)
# 발췌 본문(기존 문단 텍스트 재사용)
texts = [ptext(el) for el in old if el.tag == qn('w:p') and len(ptext(el)) > 120]
ex1, ex2, ex3 = texts[0], texts[1], texts[2]

new = []
A = new.append
A(h2('3.5 풀숲과의 연계'))
A(body("환경아카이브 풀숲에는 단체와 개인이 기증한 문서 기록과 함께, 활동 현장에서 촬영된 사진과 사진작가의 작품이 여러 컬렉션에 분산되어 있습니다. 환경사진아카이브는 이 가운데 작가 사진과 환경 이슈 현장 자료 사진을 중심으로 사진 기록을 체계적으로 수집·분류·정리·보존하는 역할을 맡습니다. 풀숲이 전자·지류 문서 중심의 기록을 다룬다면, 환경사진아카이브는 사진을 작가·주제·사건 단위로 정리하여 두 아카이브가 같은 사건을 문서와 이미지로 교차 검색할 수 있게 합니다."))

# 연계 개념도 (표 기반 다이어그램)
LW, MW, RW = 3563, 1900, 3563
def dcell(content, width, fill, align='left', color=None, bold=False, size=18, border=None):
    paras = ''
    for ln in content:
        jc = '' if align == 'left' else f'<w:jc w:val="{align}"/>'
        if isinstance(ln, tuple):  # bullet-like line
            paras += f'<w:p><w:pPr><w:spacing w:after="40" w:line="264" w:lineRule="auto"/>{jc}</w:pPr>{run("•  ", color=MED, size=size)}{run(ln[0], color=color, size=size)}</w:p>'
        else:
            paras += f'<w:p><w:pPr><w:spacing w:after="40" w:line="264" w:lineRule="auto"/>{jc}</w:pPr>{run(ln, bold=bold, color=color, size=size)}</w:p>'
    bd = border or ''
    return (f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{bd}<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
            f'<w:tcMar><w:top w:w="100" w:type="dxa"/><w:left w:w="140" w:type="dxa"/><w:bottom w:w="100" w:type="dxa"/><w:right w:w="140" w:type="dxa"/></w:tcMar>'
            f'<w:vAlign w:val="center"/></w:tcPr>{paras}</w:tc>')
side_b = f'<w:tcBorders><w:left w:val="single" w:sz="4" w:space="0" w:color="{TABLE_BORDER}"/><w:right w:val="single" w:sz="4" w:space="0" w:color="{TABLE_BORDER}"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="{TABLE_BORDER}"/></w:tcBorders>'
dg = '<w:tbl>' + _tblpr(False) + _grid([LW, MW, RW])
dg += '<w:tr><w:trPr><w:cantSplit/></w:trPr>'
dg += dcell(['환경아카이브 풀숲', 'ecoarchive.org'], LW, DARK, 'center', color='FFFFFF', bold=True, size=20)
dg += dcell([''], MW, 'FFFFFF', 'center')
dg += dcell(['환경사진아카이브', 'ecophotoarchive.org'], RW, DARK, 'center', color='FFFFFF', bold=True, size=20)
dg += '</w:tr><w:tr><w:trPr><w:cantSplit/></w:trPr>'
dg += dcell([('단체·개인에 흩어져 유실될 위험이 있는 환경 분야의 시민운동·연구·사업·사례 자료 탑재',), ('전자 및 지류 문서 중심',), ('사건·단체·주제 연표(전거)와 관계 그래프로 맥락화',)], LW, BOX_BG, border=side_b)
dg += dcell(['◀  연계  ▶', '', '사건·주제 키워드 공유', '문서 ↔ 사진 교차 검색', '작가·현장 사진 상호 유입', '전시·웹진 콘텐츠 공동 활용'], MW, 'FFFFFF', 'center', color=DARK, size=17)
dg += dcell([('환경 관련 사진 자료의 체계적 수집·분류·정리·보존',), ('작가 사진 및 환경 이슈 현장 자료 사진 중심',), ('작가별 가상전시·주제 키워드 검색, 웹진 EPAZINE',)], RW, BOX_BG, border=side_b)
dg += '</w:tr></w:tbl>'
dg_el = mk(dg)
for p in dg_el.findall(qn('w:tr'))[0].iter(qn('w:p')):
    ppr = p.find(qn('w:pPr'))
    if ppr is None: ppr = mk('<w:pPr/>'); p.insert(0, ppr)
    ppr.insert(0, mk('<w:keepNext/>'))
# 가운데 셀 첫 줄('◀ 연계 ▶') 굵게
mid = dg_el.findall(qn('w:tr'))[1].findall(qn('w:tc'))[1]
first_r = mid.find(qn('w:p')).find(qn('w:r'))
first_r.find(qn('w:rPr')).insert(0, mk('<w:b/>'))
A(dg_el)
A(caption('[환경아카이브 풀숲과 환경사진아카이브의 연계 구조]'))
A(body("이러한 연계는 개별 사례에서 구체적으로 드러납니다. 온산병 사태처럼 풀숲에 활동가의 문서 기록이 남아 있는 사건에 대해 환경사진아카이브가 당시 사진을 발굴하여 나란히 놓는 경우, 《함께사는길》 30년치 게재 사진처럼 풀숲 소장 기록에 실린 현장 사진을 사진 아카이브로 옮겨 작가·사건 단위로 재정리하는 경우, 그리고 공간풀숲 전시가 두 아카이브의 자료와 작가를 함께 활용하는 경우가 대표적입니다. 아래는 웹진 EPAZINE 창간호에 실린 온산병 사례를 발췌한 것입니다."))

# 발췌 박스 (인용 서식 + 출처 라벨)
inner = (f'<w:p><w:pPr><w:spacing w:after="100"/></w:pPr>{run("발췌", bold=True, color=DARK, size=18)}'
         f'{run("  |  웹진 EPAZINE ISSUE 01 「온산병 사태를 사진으로 기록한 청년들」 (2021.7.21, 글 : 최연하)", color=GRAY, size=17)}</w:p>')
for t in (ex1, ex2):
    inner += f'<w:p><w:pPr><w:spacing w:after="100" w:line="288" w:lineRule="auto"/></w:pPr>{run(t, italic=True, size=19, color=QUOTE_TEXT)}</w:p>'
# 이미지 2장 나란히 (중첩 표)
NOB = '<w:tblBorders>' + ''.join(f'<w:{b} w:val="none" w:sz="0" w:space="0" w:color="auto"/>' for b in ['top','left','bottom','right','insideH','insideV']) + '</w:tblBorders>'
nt = ('<w:tbl>' + re.sub(r'<w:tblBorders>.*?</w:tblBorders>', NOB, _tblpr(False)).replace(f'w:w="{CONTENT_W}"', 'w:w="8400"') + _grid([4200, 4200]) + '<w:tr>')
for cap in ['이상일, 《메멘토모리》, 1990~2003', '이기명, 《어구를 거두는 사람들》, 1990~91']:
    nt += (f'<w:tc><w:tcPr><w:tcW w:w="4200" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="60" w:after="40"/></w:pPr></w:p>'
           f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="60"/></w:pPr>{run(cap, italic=True, color=GRAY, size=16)}</w:p></w:tc>')
nt += '</w:tr></w:tbl>'
inner += nt
inner += f'<w:p><w:pPr><w:spacing w:before="100" w:after="60" w:line="288" w:lineRule="auto"/></w:pPr>{run(ex3, italic=True, size=19, color=QUOTE_TEXT)}</w:p>'
cell = (f'<w:tc><w:tcPr><w:tcW w:w="{CONTENT_W}" w:type="dxa"/>'
        f'<w:tcBorders><w:left w:val="single" w:sz="20" w:space="0" w:color="{MED}"/></w:tcBorders>'
        f'<w:shd w:val="clear" w:color="auto" w:fill="{QUOTE_BG}"/>'
        '<w:tcMar><w:top w:w="120" w:type="dxa"/><w:left w:w="200" w:type="dxa"/><w:bottom w:w="120" w:type="dxa"/><w:right w:w="160" w:type="dxa"/></w:tcMar>'
        f'</w:tcPr>{inner}</w:tc>')
exb = mk('<w:tbl>' + _tblpr(False) + _grid([CONTENT_W]) + f'<w:tr>{cell}</w:tr></w:tbl>')
inner_tbl = exb.find('.//' + qn('w:tbl'))
tcs = inner_tbl.find(qn('w:tr')).findall(qn('w:tc'))
tcs[0].find(qn('w:p')).append(img_lee); tcs[1].find(qn('w:p')).append(img_kim)
A(exb)
A(spacer(60))
A(body("온산병 사례에서 확인되듯, 사진은 풀숲의 문서 자료와 함께 시대 상황을 더 분명하게 보여주는 동반자이자, '기록의 힘'과 '상황을 전달하는 예술 매체로서의 힘'을 갖는 독자적 기록입니다. 환경사진아카이브의 연계 역할은 풀숲 곳곳에 흩어진 이러한 사진 기록을 발굴하고 작가·사건 단위로 정리하여, 문서와 이미지가 서로를 증언하는 아카이브 생태계를 만드는 데 있습니다."))

for el in old:
    body_el.remove(el)
anchor = K[i35 - 1]
for el in new:
    anchor.addnext(el); anchor = el

p = find_para(contains='개요 · 목적과 비전 · 구축 경과 · 작가 섭외 경과 · 풀숲 연계 사례 · 사진예술계에 미친 영향')
set_para_text(p, run('3.  ', bold=True, size=19) + run('환경사진아카이브', size=19) + run('   개요 · 구축 경과 · 작가 섭외 · 풀숲 연계 · 사진예술계 영향', size=16, color=GRAY))
# ---------------------------------------------------------------
# 7. Ⅵ부 완성 및 '작성중' 정리
# ---------------------------------------------------------------
for p in body_el.iter(qn('w:p')):
    t = ptext(p)
    if 'Ⅵ.   아카이브 임팩트 (작성중)' in t:
        set_para_text(p, run('Ⅵ.   아카이브 임팩트', bold=True, color='FFFFFF', size=30))
    elif t.strip() == 'Ⅵ. 아카이브 임팩트 (작성중)':
        set_para_text(p, run('Ⅵ. 아카이브 임팩트', bold=True, size=22, color=DARK))
    elif ' (Ⅵ부는 작성 중입니다.)' in t:
        rest = t.replace(' (Ⅵ부는 작성 중입니다.)', '').split(' : ', 1)[1].replace('사진 예술(에코포토)', '사진 예술(환경사진아카이브)')
        set_para_text(p, ''.join(bt('종합 평가 (Ⅵ) : ', rest)))
    if '환경사진아카이브 5년 이용현황(Ⅲ)' in t:
        replace_in_para(p, '환경사진아카이브 5년 이용현황(Ⅲ)', '환경사진아카이브 구축·이용현황(Ⅲ)')
    if '풀숲 27만·에코포토 1.6만' in t:
        label, rest = t.split(' : ', 1)
        set_para_text(p, ''.join(bt(label + ' : ', rest.replace('에코포토 1.6만', '환경사진아카이브 1.6만'))))
    if '온라인 기록(풀숲)-사진 예술(에코포토)-물리적 공간' in t:
        replace_in_para(p, '사진 예술(에코포토)', '사진 예술(환경사진아카이브)')

# ① ② ⑤ 에 환경사진아카이브 근거 추가
def add_after(p, new_el):
    p.addnext(new_el); return new_el
p = find_para(startswith='(Ⅰ) 소장 : 환경단체·연구기관·언론 26곳')
add_after(p, bullet(bt('(Ⅲ) 사진 원자료 : ', '환경사진아카이브에 작가 95인의 사진 21,248건이 축적되어 문서 기록과 교차 검색되는 시각 원자료를 공급하며, 온산병 사진 200여 점처럼 30여 년 만에 발굴된 기록이 연구 자료로 편입되었습니다.')))
p = find_para(startswith='(Ⅰ) 소장 : 온산병·매향리·시화호·새만금')
add_after(p, bullet(bt('(Ⅲ) 사진 기록 : ', '월간 《함께사는길》 30년치 게재 사진 9,561건과 온산병 기록의 발굴 등 환경사진아카이브가 운동사의 시각 기록을 보강하고, 웹진 EPAZINE 66호가 사건과 작가를 잇는 해설 콘텐츠로 축적되었습니다.')))
p = find_para(startswith='(Ⅰ·Ⅳ) 확산 : 강의·자문·사례 발표')
add_after(p, bullet(bt('(Ⅲ) 작가 네트워크 : ', '작가 95인과의 업무협약, 코로나19·1인가구 공모전을 통한 시민 참여, 4개 도시 순회전, 에코아카이브아트센터 설립(2025)으로 사진예술계와의 협력 생태계를 형성하였습니다.')))

# 매트릭스 표 교체
K = kids()
imat = next(i for i, k in enumerate(K) if k.tag == qn('w:tbl') and ptext(k).startswith('임팩트 영역Ⅰ 구축·소장·확산'))
newmat = table([1900, 2400, 2400, 2326], ['임팩트 영역', 'Ⅰ 구축·소장·확산', 'Ⅱ·Ⅲ·Ⅳ 정량 근거', 'Ⅴ 인터뷰'], [
    ['학술·지식 생산', '11만 건 원자료·사진 2.1만 건·논문 공모', '사례 검색 유입·데스크톱 우위', '심성보 "최대 강점"'],
    ['사회·운동사', '운동사 사건·전거·관계그래프·온산병 사진 발굴', '상징 사건 검색·중장년 확장·기록 발굴 전시', '경험 단절 해소·사회적 자산화'],
    ['정책·제도', '국가기록원 정책 연계', '—', '공공-민간 연계·통합 포털'],
    ['이용자 경험', '다양한 콘텐츠·큐레이션·웹진 66호', '29만 도달·재방문·균형 분포·오프라인 포용', '이용자별 가치 정리·"존재 자체의 의미"(주현미)'],
    ['조직·운영', '대외활동·공간풀숲·작가 95인 협약·수상', '14개 전시·기업 협력', '파트너 단체 기록문화 촉발'],
], aligns=['L', 'L', 'L', 'L'])
K[imat].addnext(newmat); body_el.remove(K[imat])

# 향후 과제 문단 갱신
p = find_para(startswith='본 보고서는 정량 접속통계(풀숲 6년·에코포토 5년)')
if p is not None:
    set_para_text(p, run("본 보고서는 정량 접속통계(풀숲 6년·환경사진아카이브 5년), 환경사진아카이브 구축 실적(2020~2025), 오프라인 전시 기록(공간풀숲 1년), 전문가 인터뷰 2건을 결합한 통합 임팩트 측정 결과입니다. 이용자 설문은 설계 후 시행하지 않기로 하여 인터뷰 확대로 대체하며, 다음 단계로는 인터뷰 대상을 활동가·활용 연구자·참여 작가로 넓혀 다섯 임팩트 영역 전반의 정성 근거를 보강합니다. 나아가 활동가 생애 구술을 축적하고 문서형에서 데이터형(API) 제공으로 전환하며, 세 플랫폼(온라인 기록·사진·공간)을 관통하는 아카이브 맞춤형 임팩트 지표를 개발함으로써, 정량 데이터와 정성 서사가 결합된 풀숲 고유의 임팩트 측정 체계를 완성하는 것을 목표로 합니다."))


# ---------------------------------------------------------------
# v0.6 : 문구 수정 + Ⅲ·Ⅵ부 분석 보강 (Ⅰ-3 확장 내용 반영)
# ---------------------------------------------------------------
def box_add_para(box_tbl, text):
    tc = box_tbl.find('.//' + qn('w:tc'))
    tc.append(mk(f'<w:p><w:pPr><w:spacing w:before="80" w:line="288" w:lineRule="auto"/></w:pPr>{run(text, size=19)}</w:p>'))
def find_el(contains):
    for el in kids():
        if contains in ptext(el): return el
    return None

# 1·2·4 문구
p = find_para(contains='NOTICE로 구성되고,')
replace_in_para(p, '메타데이터를 제공합니다. ABOUT·PHOTOGRAPHER', '메타데이터를 제공합니다. 아카이브는 ABOUT·PHOTOGRAPHER')
p = find_para(contains='"사진가 46인의 환경작품 1만여 점"을 보도')
replace_in_para(p, '"사진가 46인의 환경작품 1만여 점"을 보도', '"사진가 46인의 환경작품 1만여 점 공개"를 보도')
p = find_para(contains='(자료 정리 : 숲과나눔 이지현')
replace_in_para(p, ' (자료 정리 : 숲과나눔 이지현, 2026.8.14 기준)', '')

# Ⅲ-3 도달 : 구축·홍보 활동과의 연동
p = find_para(startswith='개설 첫해의 페이지 조회수')
p.addnext(body("이 추이는 Ⅰ부 3장과 Ⅲ부 1장의 구축·확산 활동과 겹쳐 읽을 때 의미가 분명해집니다. 첫해의 높은 조회수는 오픈 언론 보도 14건과 코로나19 사진전 《거리의 기술》 4개 도시 순회(2021.4~10)가 만든 초기 관심을, 2022-23년의 비교적 높은 이벤트 수는 SNS 게시물 41건과 《800번의 귀향》 전시(2022.6)를, 2024-25년의 최고점은 《함께사는길》 사진 9,561건의 대량 등록과 2024년 한 해 18호가 발행된 웹진의 누적 효과를 각각 반영합니다. 1차 구축으로 분야 주요 작가 대부분이 참여를 마친 2022년 이후에는 연 3~8인의 추가 참여와 웹진 연재가 이어지는 안정 운영 단계에 들어섰고, 개관 초기의 집중 홍보 효과가 잦아든 2025-26년에는 사용자가 초기 대비 1.7배 수준으로 정상화되었습니다. 대량 등록·전시·홍보 같은 콘텐츠 갱신 활동과 도달 규모가 같은 방향으로 움직이는 관계가 확인됩니다."))

# Ⅲ-4 유입 : 인사이트 ⑨ 보강
box_add_para(find_el('핵심 인사이트 ⑨'), "Referral 유입이 2023-24년(519명)에 정점을 이룬 것은 1인가구 사진 공모전과 웹진 EPA ARTIST 연재가 외부 매체·작가 개인 채널에 링크되던 시기와 일치하며, Organic Social의 감소는 개관 첫해에 집중되었던 SNS 홍보가 자연스럽게 줄어든 결과로 해석됩니다. 5년 누적 Direct 6,523명은 작가 95인과 파트너 단체가 자신의 작품·자료를 찾아오는 '참여자 기반 재방문'의 규모를 보여줍니다.")

# Ⅲ-5 콘텐츠 활용 : 웹진 시리즈·교차 아카이브 발견
p = find_para(startswith='5년 내내 압도적 1위 콘텐츠는')
p.addnext(body("웹진 EPAZINE 66호 가운데 작가를 소개하는 EPA ARTIST 연재(28호)는 작가 페이지로 이용자를 이끄는 관문 역할을 하였고, 환경 이슈 해설(새만금·매향리 등)과 전시 리뷰는 풀숲의 문서 기록과 같은 사건 축을 공유합니다. 특히 온산병은 풀숲의 2025-26년 Google 검색 유입 상위 키워드(98회)이자 환경사진아카이브의 5년 스테디셀러(ISSUE 01)로, 하나의 사건이 문서 아카이브와 사진 아카이브 양쪽에서 검색·열람되는 교차 발견의 실증 사례입니다."))

# Ⅲ-5 인사이트 ⑩ 보강
box_add_para(find_el('핵심 인사이트 ⑩'), "환경사진 분야의 주요 작가 대부분이 이미 참여한 만큼 작가 수의 확대에는 한계가 있으며, 이 구조에서 도달을 지탱하는 것은 기존 작가의 신작·미공개 작업 추가와 웹진 신규 호처럼 작가 페이지를 다시 찾게 만드는 콘텐츠 갱신입니다. 작가 페이지 조회가 2024-25년 7,054회에서 2025-26년 5,718회로 조정된 것은 갱신 주기와 도달의 관계를 살펴볼 지표가 됩니다.")

# Ⅵ-1 ④ 이용자 경험 : 사진아카이브 이용 특성·오프라인 참여 선례
p = find_para(startswith='(Ⅱ·Ⅲ) 통계 : 세 플랫폼')
p.addnext(bullet(bt('(Ⅰ·Ⅲ) 사진 아카이브 : ', '환경사진아카이브는 체류 이벤트 비율 91.6%, 모바일 42%, 해외 접속 15%의 감상형 이용 양상으로 풀숲과 다른 수용자층을 열었고, 공간풀숲 개관 이전에도 코로나19 사진전 4개 도시 순회, 시민 공모 230여 명 응모, 《800번의 귀향》 관객 500여 명 등 오프라인 시민 참여의 선례를 축적하였습니다.')))

# Ⅵ-2 한계 : 공급 측 활동 정체
p = find_para(startswith='환경사진아카이브는 구글 검색어·내부 검색어')
p.addnext(bullet("환경사진아카이브는 분야 주요 작가 대부분이 참여하여 1차 구축이 완료된 성숙 단계에 있어, 도달 지표가 신규 작가 수보다 콘텐츠 갱신 활동에 연동되는 구조(Ⅲ부 1·5장)입니다. 2024년의 대량 등록(《함께사는길》 9,561건)은 기록사진 성격이 강해 작가 아카이브의 확장과는 구분하여 평가할 필요가 있으며, 갱신 활동의 효과를 추적할 수 있는 지표(작가별 신작 추가 건수, 웹진 호별 조회)의 정비가 필요합니다."))

# Ⅵ-3 향후 과제 : 공급 측 활동 재개
p = find_para(startswith='본 보고서는 정량 접속통계(풀숲 6년·환경사진아카이브 5년)')
p.addnext(body("환경사진아카이브에 대해서는 Ⅲ부에서 확인된 '콘텐츠 갱신–도달 규모'의 연동 관계에 따라, 기존 참여 작가의 신작·미공개 작업 추가 수집, 현장 활동가·시민 사진 등 새로운 자료원의 발굴, 웹진 EPAZINE과 공간풀숲 전시의 연계 발행을 과제로 제시합니다. 아울러 온산병 사례처럼 풀숲의 문서 기록과 사진 기록을 사건 단위로 묶어 교차 검색·교차 전시하는 연계 콘텐츠를 정례화하여, 두 아카이브가 서로의 유입 경로가 되는 구조를 강화할 필요가 있습니다."))

# 맺음말 보강
box_add_para(find_el('맺음말 — 디지털 아카이브의 사회적 가치'), "특히 환경사진아카이브는 작가 95인·사진 2만 1천여 건의 축적과 함께 '환경사진'이라는 범주를 사회적으로 성립시켰고, 30여 년 만에 발굴된 온산병 사진처럼 문서와 이미지가 서로를 증언하는 기록 생태계의 가능성을 보여주었습니다. 이 축적 위에 작가·웹진·전시로 이어지는 콘텐츠 갱신이 다음 6년의 임팩트를 넓혀갈 것입니다.")

# Executive Summary Ⅲ 항목 한 문장 추가
p = find_para(startswith='환경사진아카이브 구축·이용현황 (Ⅲ)')
t = ptext(p).split(' : ', 1)[1]
set_para_text(p, ''.join(bt('환경사진아카이브 구축·이용현황 (Ⅲ) : ', t + ' 이용 규모는 대량 등록·전시·홍보 등 콘텐츠 갱신 활동과 같은 방향으로 움직이며, 주요 작가 대부분이 참여를 마친 성숙 단계에서는 갱신의 리듬이 도달을 좌우하는 것으로 분석됩니다.')))

# ---------------------------------------------------------------
# 1. 헤더/푸터 : 짝수(왼쪽) 쪽수+보고서명 / 홀수(오른쪽) 장 이름+쪽수, 하단 쪽수 삭제
# ---------------------------------------------------------------
# ChapterTitle 스타일 정의 (STYLEREF 용)
styles_el = doc.styles.element
if styles_el.find(f'.//{qn("w:style")}[@{qn("w:styleId")}="ChapterTitle"]') is None:
    styles_el.append(mk('<w:style w:type="paragraph" w:customStyle="1" w:styleId="ChapterTitle"><w:name w:val="ChapterTitle"/>'
                        '<w:basedOn w:val="a"/><w:qFormat/><w:pPr><w:keepNext/><w:outlineLvl w:val="1"/></w:pPr></w:style>'))
    styles_el.append(mk('<w:style w:type="paragraph" w:customStyle="1" w:styleId="PartTitle"><w:name w:val="PartTitle"/>'
                        '<w:basedOn w:val="a"/><w:qFormat/><w:pPr><w:keepNext/><w:outlineLvl w:val="0"/></w:pPr></w:style>'))
# 장 제목(괘선 문단) + 부 표지 문단에 스타일 적용
def is_chapter(p):
    b = p.find(qn('w:pPr'))
    return b is not None and b.find(qn('w:pBdr')) is not None and b.find(qn('w:pBdr')).find(qn('w:bottom')) is not None \
        and b.find(qn('w:pBdr')).find(qn('w:bottom')).get(qn('w:color')) == MED \
        and b.find(qn('w:pBdr')).find(qn('w:bottom')).get(qn('w:sz')) == '12' and p.getparent().tag == qn('w:body')
def apply_style(p, name='ChapterTitle'):
    ppr = p.find(qn('w:pPr'))
    if ppr is None: ppr = mk('<w:pPr/>'); p.insert(0, ppr)
    if ppr.find(qn('w:pStyle')) is not None: ppr.remove(ppr.find(qn('w:pStyle')))
    ppr.insert(0, mk(f'<w:pStyle w:val="{name}"/>'))
FRONT = ('목차', 'Executive Summary', '부록.')
toc_targets = []  # (title_text, paragraph)
for el in kids():
    if el.tag == qn('w:p') and is_chapter(el):
        apply_style(el, 'PartTitle' if ptext(el).startswith(FRONT) else 'ChapterTitle'); toc_targets.append(el)
    elif el.tag == qn('w:tbl'):
        t = ptext(el)
        if re.match(r'^[ⅠⅡⅢⅣⅤⅥ]\.\s', t) and len(t) < 60:
            p = el.find('.//' + qn('w:p')); apply_style(p, 'PartTitle'); toc_targets.append(p)

sec = doc.sections[0]
doc.settings.odd_and_even_pages_header_footer = True
sec.different_first_page_header_footer = True
BORDER = f'<w:pBdr><w:bottom w:val="single" w:sz="4" w:space="4" w:color="{GRAY_BORDER}"/></w:pBdr>'
def num_run(): return f'<w:fldSimple w:instr=" PAGE "><w:r>{rpr(bold=True, size=19, color=DARK)}<w:t>1</w:t></w:r></w:fldSimple>'
def title_run(): return f'<w:fldSimple w:instr=" STYLEREF &quot;PartTitle&quot; \\* MERGEFORMAT "><w:r>{rpr(size=15, color=GRAY)}<w:t>장</w:t></w:r></w:fldSimple>'
def set_header(hdr, xml):
    hel = hdr._element
    for ch in list(hel): hel.remove(ch)
    hel.append(mk(xml))
def clear_footer(ftr):
    fel = ftr._element
    for ch in list(fel): fel.remove(ch)
    fel.append(mk('<w:p/>'))
even_xml = f'<w:p><w:pPr>{BORDER}<w:spacing w:after="240"/></w:pPr>{num_run()}{run("   환경아카이브 풀숲 임팩트 측정 보고서", size=15, color=GRAY)}</w:p>'
odd_xml = f'<w:p><w:pPr>{BORDER}<w:spacing w:after="240"/><w:jc w:val="right"/></w:pPr>{title_run()}{run("   ", size=15)}{num_run()}</w:p>'
set_header(sec.header, odd_xml)          # 기본 = 홀수(오른쪽) 페이지
set_header(sec.even_page_header, even_xml)
set_header(sec.first_page_header, '<w:p/>')
clear_footer(sec.footer); clear_footer(sec.even_page_footer); clear_footer(sec.first_page_footer)

# ---------------------------------------------------------------
# 8. 보고서 정보 페이지 (문서 끝)
# ---------------------------------------------------------------
sectPr = body_el.find(qn('w:sectPr'))
def colophon_line(label, value, last=False):
    return para(run(label, bold=True, size=15, color=MED) + f'<w:r><w:tab/></w:r>' + run(value, size=15, color=TEXT),
                '<w:tabs><w:tab w:val="left" w:pos="1500"/></w:tabs><w:ind w:left="1500" w:hanging="1500"/>'
                f'<w:spacing w:after="{"60" if not last else "0"}" w:line="300" w:lineRule="auto"/>')
rule = lambda: para('', f'<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="{MED}"/></w:pBdr><w:spacing w:after="160"/>')
info = [page_break(), spacer(5200),
        para(run('보고서 정보', bold=True, size=15, color=GRAY), '<w:spacing w:after="60"/>'),
        para(run('환경아카이브 풀숲 · 환경사진아카이브 · 공간풀숲', bold=True, size=19, color=DARK), '<w:spacing w:after="20"/>'),
        para(run('임팩트 측정 보고서', bold=True, size=24, color=DARK), '<w:spacing w:after="120"/>'),
        rule(),
        colophon_line('작성', '이지현  재단법인 숲과나눔 사무처장'),
        colophon_line('', '최연하  에코아카이브아트센터 총괄감독'),
        colophon_line('', '안대진  아카이브랩 대표'),
        spacer(60),
        colophon_line('발행일', '2026년 10월 1일'),
        colophon_line('발행', '재단법인 숲과나눔'),
        spacer(60),
        colophon_line('분석 기간', '환경아카이브 풀숲 2020.06~2026.05  ·  환경사진아카이브 2021.07~2026.06  ·  공간풀숲 2025.07~2026.08'),
        colophon_line('데이터 출처', 'Google Analytics (UA·GA4)  ·  Omeka DB  ·  전시 기록 정성·정량 평가  ·  전문가 인터뷰(FGI)'),
        spacer(60),
        colophon_line('AI 활용 범위', '접속통계·소장 DB·전시 기록 데이터의 집계와 차트 작성, 초안 문장 작성·편집과 서식 구성에 생성형 AI(Anthropic Claude)를 활용하였습니다. 데이터 해석의 방향 설정, 사실 확인, 전문가 인터뷰, 최종 내용의 검토·확정은 작성자가 수행하였습니다.', last=True),
        spacer(120), rule()]
for el in info: sectPr.addprevious(el)

# 표지 버전
for p in body_el.iter(qn('w:p')):
    if ptext(p).strip() in ('v0.4',): set_para_text(p, run('v0.9  ·  2026년 10월 1일 발행'))

doc.save(OUT)
print('stage1 saved; toc targets:', len(toc_targets))

# ---------------------------------------------------------------
# 2. 목차 쪽수: LibreOffice 렌더링으로 쪽수 산출 → 북마크 + PAGEREF(캐시값) 삽입
# ---------------------------------------------------------------
subprocess.run(['python', '/mnt/skills/public/docx/scripts/office/soffice.py', '--headless', '--convert-to', 'pdf', OUT],
               capture_output=True, cwd='/home/claude')
pdf = OUT.replace('.docx', '.pdf')
import pypdf
pages = [pg.extract_text() or "" for pg in pypdf.PdfReader(pdf).pages]
norm = lambda s: re.sub(r'\s+', '', s)
page_texts = [norm(t) for t in pages]

doc = Document(OUT); body_el = doc.element.body
# 대상 문단 다시 찾기 (스타일 기준)
targets = [p for p in body_el.iter(qn('w:p')) if (p.find(qn('w:pPr')) is not None and p.find(qn('w:pPr')).find(qn('w:pStyle')) is not None
           and p.find(qn('w:pPr')).find(qn('w:pStyle')).get(qn('w:val')) in ('ChapterTitle', 'PartTitle'))]
bm_id = 100
title_page = {}
last_pg = 0
for p in targets:
    t = norm(ptext(p))
    if not t: continue
    key = t[:14]
    pg = None
    for pi in range(max(last_pg, 1 if key.startswith('목차') else 2), len(page_texts)):   # 목차 이후에서 검색
        if key in page_texts[pi]:
            pg = pi + 1; break
    if pg: last_pg = pg - 1
    # 북마크
    bm_id += 1
    name = f'_ch{bm_id}'
    p.insert(1 if p.find(qn('w:pPr')) is not None else 0, mk(f'<w:bookmarkStart w:id="{bm_id}" w:name="{name}"/>'))
    p.append(mk(f'<w:bookmarkEnd w:id="{bm_id}"/>'))
    title_page[t] = (name, pg)
print({k[:12]: v for k, v in title_page.items()})

# 목차 항목에 쪽수 필드 추가
def match_target(entry_text):
    e = norm(entry_text)
    m = re.match(r'^([ⅠⅡⅢⅣⅤⅥ]\.|\d+\.|부록\.|Executive|A~E)(.*)$', e)
    for t, v in title_page.items():
        tt = t
        if e.startswith('Executive') and tt.startswith('Executive'): return v
        if e.startswith('부록') and tt.startswith('부록'): return v
        if e.startswith('A~E'): return None
        if m and (m.group(1).startswith(('Ⅰ', 'Ⅱ', 'Ⅲ', 'Ⅳ', 'Ⅴ', 'Ⅵ'))):
            if tt.startswith(m.group(1)) and norm(m.group(2))[:6] in tt: return v
    return None

K = kids()
itoc = next(i for i, k in enumerate(K) if ptext(k).strip() == '목차')
iend = next(i for i, k in enumerate(K) if i > itoc and ptext(k).startswith('Executive Summary') and is_chapter(k) is False and K[i].find(qn('w:pPr')).find(qn('w:pStyle')) is not None) if False else None
# 목차 범위: '목차' 다음부터 다음 ChapterTitle 스타일 문단 전까지
cur_part = None
for k in K[itoc + 1:]:
    if k.tag != qn('w:p'): continue
    ppr = k.find(qn('w:pPr'))
    if ppr is not None and ppr.find(qn('w:pStyle')) is not None and ppr.find(qn('w:pStyle')).get(qn('w:val')) in ('ChapterTitle', 'PartTitle'): break
    txt = ptext(k).strip()
    if not txt: continue
    m = re.match(r'^([ⅠⅡⅢⅣⅤⅥ])\.', txt)
    if m: cur_part = m.group(1)
    # 대상 결정
    v = None
    e = norm(txt)
    if e.startswith('Executive'): v = next((vv for t, vv in title_page.items() if t.startswith('Executive')), None)
    elif e.startswith('부록'): v = next((vv for t, vv in title_page.items() if t.startswith('부록')), None)
    elif m: v = next((vv for t, vv in title_page.items() if t.startswith(m.group(1) + '.') and e[2:8] in t), None)
    elif re.match(r'^\d+\.', e) and cur_part:
        num = re.match(r'^(\d+)\.', e).group(1)
        # 해당 부 이후의 장 제목 중 번호 일치
        part_idx = [i for i, (t, vv) in enumerate(title_page.items()) if t.startswith(cur_part + '.')]
        items = list(title_page.items())
        if part_idx:
            for t, vv in items[part_idx[0] + 1:]:
                if re.match(r'^[ⅠⅡⅢⅣⅤⅥ]\.', t): break
                if t.startswith(num + '.'): v = vv; break
    if not v or not v[1]: continue
    name, pg = v
    if ppr is None: ppr = mk('<w:pPr/>'); k.insert(0, ppr)
    ppr.append(mk('<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9026"/></w:tabs>'))
    k.append(mk('<w:r><w:tab/></w:r>'))
    k.append(mk(f'<w:fldSimple w:instr=" PAGEREF {name} \\h "><w:r>{rpr(bold=True, size=19)}<w:t>{pg}</w:t></w:r></w:fldSimple>'))

# Word 열 때 필드 갱신
st = doc.settings.element
uf = st.find(qn('w:updateFields'))
if uf is not None: st.remove(uf)
doc.save(OUT)
print('done')
