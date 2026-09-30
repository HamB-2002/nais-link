import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np, os
font_manager.fontManager.addfont('/home/claude/NotoSansCJKkr.ttf'); font_manager.fontManager.addfont('/home/claude/NotoSansCJKkr-Bold.ttf')
plt.rcParams['font.family'] = 'Noto Sans CJK KR'; plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['axes.spines.top'] = False; plt.rcParams['axes.spines.right'] = False
D = '/home/claude/sitedata/'; OUT = '/home/claude/media/'
G1, G2, G3, G4 = '#2E6E3F', '#4C9A5A', '#8FCB94', '#CFE7D1'
PAL = ['#2E6E3F', '#4C9A5A', '#8FCB94', '#F4D06F', '#EE9B4A', '#D9534F', '#7A6FB0', '#5F9EA0', '#B26B1F', '#9AA79C', '#C9B27A', '#D5D5D5']
h = json.load(open(D + 'holdings.json')); C = json.load(open(D + 'collections.json'))
win = json.load(open(D + 'keywords_windows.json')); life = json.load(open(D + 'keywords_life.json'))
chg = json.load(open(D + 'keywords_change.json')); ok = json.load(open(D + 'org_keywords.json'))
NEWS = {'정치', '경제', '문화', '과학', '사회', '국제', '스포츠', '생활', '지역', '사설', '칼럼', '월간지', '소식지'}
def kv(lst): return {x['k']: x['v'] for x in lst}
def save(name): plt.tight_layout(); plt.savefig(OUT + name, dpi=150); plt.close()

# F1 컬렉션별 등록·공개
cs = [c for c in C if c['total'] >= 30]
names = [c['name'] for c in cs][::-1]; tot = [c['total'] for c in cs][::-1]; pub = [c['public'] for c in cs][::-1]
fig, ax = plt.subplots(figsize=(8.6, 7.2))
ax.barh(names, tot, color=G4, height=0.7, label='등록(비공개 포함)'); ax.barh(names, pub, color=G1, height=0.7, label='공개')
for i, (t, p) in enumerate(zip(tot, pub)): ax.text(t + 150, i, f'{p:,} / {t:,}', va='center', fontsize=8, color='#333')
ax.set_xlim(0, 21500); ax.legend(frameon=False, fontsize=9, loc='lower right'); ax.tick_params(labelsize=8.5); ax.set_xlabel('기록 수 (공개 / 등록)', fontsize=9)
save('F1_coll_count.png')

# helper: stacked 100% horizontal by collection
def stacked(name, key, cats, colors, min_total=100, top=None, order=None):
    cs2 = [c for c in C if c['total'] >= min_total]
    if top: cs2 = cs2[:top]
    rows = []
    for c in cs2:
        d = kv(c[key]); s = sum(d.get(k, 0) for k in cats)
        if s == 0: continue
        rows.append((c['name'], [d.get(k, 0) / s * 100 for k in cats]))
    rows = rows[::-1]
    fig, ax = plt.subplots(figsize=(8.6, 0.28 * len(rows) + 1.3))
    left = np.zeros(len(rows)); ys = [r[0] for r in rows]
    for j, k in enumerate(cats):
        vals = np.array([r[1][j] for r in rows])
        ax.barh(ys, vals, left=left, color=colors[j], height=0.72, label=k)
        for i, (l, v) in enumerate(zip(left, vals)):
            if v >= 12: ax.text(l + v / 2, i, f'{v:.0f}', ha='center', va='center', fontsize=7.5, color='white' if j < 2 else '#333')
        left += vals
    ax.set_xlim(0, 100); ax.tick_params(labelsize=8.5); ax.set_xlabel('구성비 (%)', fontsize=9)
    ax.legend(frameon=False, fontsize=8, ncol=min(len(cats), 6), loc='upper center', bbox_to_anchor=(0.5, -0.09 if len(rows) > 15 else -0.18))
    save(name)

stacked('F2_coll_rtype.png', 'rtype', ['문서류', '도서간행물류', '사진그림류', '영상음성류', '특수전자기록물류'], [G1, G2, '#F4D06F', '#EE9B4A', '#7A6FB0'], min_total=100)
stacked('F3_coll_decade.png', 'decade', ['1980s', '1990s', '2000s', '2010s', '2020s'], ['#1F4D2C', G1, G2, G3, '#F4D06F'], min_total=100)
stacked('F4_coll_subject.png', 'subject', ['반공해', '반핵탈핵', '생태계보전', '기후에너지', '자원순환', '생활안전', '대기오염', '일반'],
        ['#7A6FB0', '#D9534F', G1, '#EE9B4A', '#F4D06F', '#5F9EA0', '#9AA79C', '#D5D5D5'], min_total=100)
# F5 지역 (지역 식별 기록 100건 이상 컬렉션)
regs = ['서울', '전북', '경기', '제주', '강원', '경남', '인천', '전남', '경북', '충남']
rows = []
for c in C:
    d = kv(c['regions']); s = sum(d.values())
    if s < 60: continue
    rows.append((c['name'], [d.get(k, 0) / s * 100 for k in regs], 100 - sum(d.get(k, 0) for k in regs) / s * 100))
rows = rows[::-1]
fig, ax = plt.subplots(figsize=(8.6, 0.32 * len(rows) + 1.4)); left = np.zeros(len(rows)); ys = [r[0] for r in rows]
for j, k in enumerate(regs + ['기타']):
    vals = np.array([r[1][j] if j < len(regs) else r[2] for r in rows]); col = PAL[j] if j < len(regs) else '#D5D5D5'
    ax.barh(ys, vals, left=left, color=col, height=0.72, label=k)
    for i, (l, v) in enumerate(zip(left, vals)):
        if v >= 12: ax.text(l + v / 2, i, f'{v:.0f}', ha='center', va='center', fontsize=7.5, color='white' if j < 3 else '#333')
    left += vals
ax.set_xlim(0, 100); ax.tick_params(labelsize=8.5); ax.set_xlabel('지역 식별 기록 중 구성비 (%)', fontsize=9)
ax.legend(frameon=False, fontsize=8, ncol=6, loc='upper center', bbox_to_anchor=(0.5, -0.12)); save('F5_coll_region.png')

# F11 지역 분포 전체
r = h['regions'][:14]
fig, ax = plt.subplots(figsize=(8.6, 3.4)); ax.bar([x['k'] for x in r], [x['v'] for x in r], color=[G1 if i < 5 else G3 for i in range(len(r))], width=0.62)
for i, x in enumerate(r): ax.text(i, x['v'] + 25, f"{x['v']:,}", ha='center', fontsize=8.5)
ax.set_ylabel('기록 수 (키워드·태그 기준 추정)', fontsize=9); ax.tick_params(labelsize=9); save('F11_region.png')

# F6 연도별 생산기록
yr = kv(h['year']); ys = list(range(1980, 2026)); vs = [yr.get(y, 0) for y in ys]
fig, ax = plt.subplots(figsize=(8.6, 3.6)); ax.bar(ys, vs, color=[G1 if 1990 <= y <= 2009 else G2 for y in ys], width=0.8)
ax.axvline(1981.5, color='#9AA79C', ls='--', lw=1); ax.text(1982, max(vs) * 0.92, '1982 (연 30건 이상 시작)', fontsize=8, color='#555')
pk = max(vs); ax.text(1999, pk + 60, f'1999 정점 {pk:,}건', ha='center', fontsize=8.5, color=G1)
ax.set_ylabel('기록 수', fontsize=9); ax.set_xlim(1979, 2026); ax.tick_params(labelsize=9); save('F6_year.png')

# F7 연대별 주제 구성비
dec = [d for d in h['subject_by_decade'] if d['decade'] in ['1980s', '1990s', '2000s', '2010s', '2020s']]
cats = ['반공해', '반핵탈핵', '생태계보전', '기후에너지', '자원순환', '생활안전', '재난재해']
cols = ['#7A6FB0', '#D9534F', G1, '#EE9B4A', '#F4D06F', '#5F9EA0', '#9AA79C']
fig, ax = plt.subplots(figsize=(8.6, 3.8)); x = [d['decade'] for d in dec]; bottom = np.zeros(len(dec))
for k, col in zip(cats, cols):
    vals = np.array([d.get(k, 0) / sum(d.get(c, 0) for c in cats) * 100 for d in dec])
    ax.bar(x, vals, bottom=bottom, color=col, width=0.6, label=k)
    for i, (b, v) in enumerate(zip(bottom, vals)):
        if v >= 6: ax.text(i, b + v / 2, f'{v:.0f}%', ha='center', va='center', fontsize=8, color='white' if col in (G1, '#7A6FB0', '#D9534F') else '#333')
    bottom += vals
ax.set_ylim(0, 100); ax.set_ylabel('구성비 (%)', fontsize=9); ax.legend(frameon=False, fontsize=8, ncol=7, loc='upper center', bbox_to_anchor=(0.5, -0.08)); ax.tick_params(labelsize=9)
save('F7_decade_subject.png')

# decade merge helper for keywords
DEC = {'1980s': ['1980-1989'], '1990s': ['1990-1994', '1995-1999'], '2000s': ['2000-2004', '2005-2009'], '2010s': ['2010-2014', '2015-2019'], '2020s': ['2020-2024']}
W = {w['win']: w for w in win}
def dec_top(field, key, n):
    out = {}
    for d, ws in DEC.items():
        agg = {}
        for wn in ws:
            for x in W[wn][field]:
                if x['k'] in NEWS: continue
                agg[x['k']] = agg.get(x['k'], 0) + x[key]
        out[d] = sorted(agg.items(), key=lambda t: -t[1])[:n]
    return out
def panels(name, data, xlabel):
    fig, axes = plt.subplots(1, 5, figsize=(8.6, 4.2))
    for ax, (d, items) in zip(axes, data.items()):
        ks = [k for k, v in items][::-1]; vs = [v for k, v in items][::-1]
        ax.barh(ks, vs, color=G2, height=0.65); ax.set_title(d, fontsize=10, color=G1, loc='left'); ax.tick_params(labelsize=7.5); ax.set_xticks([])
        for i, v in enumerate(vs): ax.text(v, i, f' {v:g}', va='center', fontsize=6.5, color='#555')
        ax.set_xlim(0, max(vs) * 1.35)
    fig.text(0.5, 0.005, xlabel, ha='center', fontsize=8, color='#555'); plt.tight_layout(rect=(0, 0.02, 1, 1)); plt.savefig(OUT + name, dpi=150); plt.close()
panels('F9_decade_topkw.png', dec_top('top', 'v', 10), '연대별 출현 건수 상위 10개 키워드 (한겨레 지면 분류어 제외)')
panels('F8_decade_distinct.png', dec_top('distinct', 'score', 8), '연대별 특징 키워드 (전체 대비 출현 비율, 상위 8개)')

# F13 범프차트 (5년 단위 상위 10 순위)
wins = [w['win'] for w in win]; TOPN = 10
ranks = {}
for wi, w in enumerate(win):
    ks = [x['k'] for x in w['top'] if x['k'] not in NEWS][:TOPN]
    for r, k in enumerate(ks): ranks.setdefault(k, {})[wi] = r + 1
fig, ax = plt.subplots(figsize=(8.6, 5.8)); ci = 0
for k, rs in ranks.items():
    xs = sorted(rs); col = PAL[ci % len(PAL)]; ci += 1
    ax.plot(xs, [rs[x] for x in xs], marker='o', ms=4, lw=1.4, color=col, alpha=0.9)
    x_last = xs[-1]; y_last = rs[x_last]
    if x_last == len(wins) - 1:
        ax.text(x_last + 0.1, y_last, k, fontsize=7, va='center', color=col)
    else:
        ax.annotate(k, (x_last, y_last), xytext=(4, 4), textcoords='offset points', fontsize=6.3, color=col)
ax.set_xticks(range(len(wins))); ax.set_xticklabels(wins, fontsize=8); ax.set_yticks(range(1, TOPN + 1)); ax.invert_yaxis(); ax.set_ylabel('순위', fontsize=9); ax.set_xlim(-0.4, len(wins) + 0.9)
ax.grid(axis='y', color='#EEE'); save('F13_bump.png')

# F14 키워드 생애 (상위 40)
lf = [x for x in life if x['k'] not in NEWS]; lf = sorted(lf, key=lambda x: -x['n'])[:40]; lf = sorted(lf, key=lambda x: x['peak'])[::-1]
fig, ax = plt.subplots(figsize=(8.6, 8.0))
for i, x in enumerate(lf):
    ax.plot([x['first'], x['last']], [i, i], color=G3, lw=5, solid_capstyle='butt'); ax.plot(x['peak'], i, 'o', color=G1, ms=6)
    ax.text(x['last'] + 0.4, i, f"{x['k']} ({x['n']:,})", va='center', fontsize=7.5)
ax.set_yticks([]); ax.set_xlim(1979, 2038); ax.tick_params(labelsize=9); ax.set_xlabel('출현 연도 범위 (막대) · 최다 출현 연도 (점) · 괄호는 출현 건수', fontsize=9); ax.grid(axis='x', color='#EEE')
save('F14_life.png')

# F15 급상승·급락
pairs = [('1990s', '2000s'), ('2000s', '2010s'), ('2010s', '2020s')]
fig, axes = plt.subplots(1, 3, figsize=(8.6, 4.6))
for ax, (a, b) in zip(axes, pairs):
    sub = [x for x in chg if x['from'] == a and x['to'] == b and x['k'] not in NEWS and (x['a'] + x['b']) >= 40]
    up = sorted(sub, key=lambda x: -x['ratio'])[:8]; dn = sorted(sub, key=lambda x: x['ratio'])[:8]
    items = dn[::-1] + up[::-1] if False else up + dn[::-1]
    ks = [x['k'] for x in items][::-1]; vs = [x['ratio'] for x in items][::-1]
    ax.barh(ks, vs, color=[G1 if v > 0 else '#D9534F' for v in vs], height=0.65); ax.axvline(0, color='#999', lw=0.8)
    ax.set_title(f'{a} → {b}', fontsize=10, color=G1, loc='left'); ax.tick_params(labelsize=7.5); ax.set_xlabel('log2 점유율 변화', fontsize=8)
save('F15_change.png')

# F10 월별 등록 추이
am = h['added_month']; ks = [x['k'] for x in am]; vs = [x['v'] for x in am]
fig, ax = plt.subplots(figsize=(8.6, 3.6)); ax.bar(range(len(ks)), vs, color=[G1 if v > 4000 else G3 for v in vs], width=0.8)
for i, v in enumerate(vs):
    if v > 4000: ax.text(i, v + 300, f'{ks[i]}\n{v:,}', ha='center', fontsize=7, color='#333')
step = max(1, len(ks) // 12); ax.set_xticks(range(0, len(ks), step)); ax.set_xticklabels([ks[i] for i in range(0, len(ks), step)], fontsize=8, rotation=45, ha='right')
ax.set_ylabel('등록 아이템 수', fontsize=9); ax.set_ylim(0, max(vs) * 1.25); save('F10_added_month.png')

# F12 단체 × 키워드 히트맵
M = np.array(ok['matrix']); orgs = ok['orgs']; kws = ok['keywords'][:28]; M = M[:, :len(kws)] * 100
fig, ax = plt.subplots(figsize=(8.6, 5.6)); im = ax.imshow(M, cmap='Greens', aspect='auto', vmax=np.percentile(M, 97))
ax.set_xticks(range(len(kws))); ax.set_xticklabels(kws, rotation=60, ha='right', fontsize=7.5); ax.set_yticks(range(len(orgs))); ax.set_yticklabels(orgs, fontsize=8)
cb = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02); cb.set_label('컬렉션 내 출현 비율 (%)', fontsize=8); cb.ax.tick_params(labelsize=7)
ax.spines[['top', 'right']].set_visible(True); save('F12_org_kw.png')
print('figures done:', sorted(f for f in os.listdir(OUT) if f.startswith('F')))
