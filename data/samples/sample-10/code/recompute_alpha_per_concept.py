# -*- coding: utf-8 -*-
# 보고서 4.1절 표에서 2x2 분할표를 복원해 개념별 Krippendorff's alpha 계산
N = 62
# (개념, 원본+, 재코딩+, 둘다+, 보고서기재 일치율, 보고서기재 kappa, 불일치수)
rows = [
 ("미술시장",12,5,5,0.887,0.535,7),
 ("비엔날레",8,5,4,0.919,0.573,5),
 ("AI협업",1,2,0,0.952,-0.022,3),
 ("한국현대미술",9,10,8,0.952,0.814,3),
 ("생성AI",9,7,7,0.968,0.857,2),
 ("AI윤리",3,5,3,0.968,0.734,2),
 ("예술과과학",2,0,0,0.968,0.000,2),
 ("현대미술이론",3,1,1,0.968,0.488,2),
 ("미디어아트",6,4,4,0.968,0.783,2),
 ("노동권",5,3,3,0.968,0.734,2),
 ("국내아트페어",4,3,3,0.984,0.849,1),
 ("AI저작권",2,3,2,0.984,0.792,1),
 ("기후예술",1,0,0,0.984,0.000,1),
 ("베니스비엔날레",3,3,3,1.000,1.000,0),
 ("아트페어",1,1,1,1.000,1.000,0),
 ("아트바젤홍콩",1,1,1,1.000,1.000,0),
 ("AI아트",9,9,9,1.000,1.000,0),
 ("AI교육",1,1,1,1.000,1.000,0),
 ("딥페이크",0,0,0,1.000,None,0),
 ("웹툰AI",0,0,0,1.000,None,0),
 ("퍼포먼스아트",0,0,0,1.000,None,0),
 ("공공미술",3,3,3,1.000,1.000,0),
 ("지정학",2,2,2,1.000,1.000,0),
 ("표현의자유",0,0,0,1.000,None,0),
]

def alpha_binary(a,b,c,d):
    """2코더·이진 명목자료의 Krippendorff alpha.
    a=둘다1, b=원본만1, c=재코딩만1, d=둘다0"""
    n = a+b+c+d
    npair = 2*n                      # 총 pairable values
    Do = (b+c)/n                     # 관찰 불일치
    n1 = 2*a + (b+c)                 # coincidence 주변합
    n0 = 2*d + (b+c)
    De = 2*n1*n0/(npair*(npair-1))   # 기대 불일치
    if De == 0: return None
    return 1 - Do/De

# --- 검산 1: 전체(1,488셀) alpha가 보고서의 0.7727과 맞는지 ---
A=B=C=0
for _,o,r,bo,_,_,_ in rows:
    A += bo; B += o-bo; C += r-bo
D = 24*N - A - B - C
print(f"전체 셀: a={A} b={B} c={C} d={D}  합={A+B+C+D} (기대 1488)")
print(f"불일치 b+c={B+C} (보고서 33)")
print(f"percent agreement = {(A+D)/(24*N):.4f} (보고서 0.9778)")
print(f"전체 alpha = {alpha_binary(A,B,C,D):.4f} (보고서 0.7727)")
print()

# --- 개념별 alpha ---
print(f"{'개념':<14}{'orig':>5}{'rec':>5}{'both':>5}{'일치율':>9}{'kappa':>9}{'alpha':>9}{'차이':>8}")
print("-"*66)
out=[]
for name,o,r,bo,pa,kap,nd in rows:
    a=bo; b=o-bo; c=r-bo; d=N-a-b-c
    assert b+c==nd, f"{name}: 불일치수 불일치 {b+c} vs {nd}"
    assert abs((a+d)/N - pa) < 0.002, f"{name}: 일치율 불일치"
    al = alpha_binary(a,b,c,d)
    out.append((name,al,kap))
    als = f"{al:.3f}" if al is not None else "N/A"
    kps = f"{kap:.3f}" if kap is not None else "N/A"
    dif = f"{al-kap:+.4f}" if (al is not None and kap is not None) else "—"
    print(f"{name:<14}{o:>5}{r:>5}{bo:>5}{(a+d)/N*100:>8.1f}%{kps:>9}{als:>9}{dif:>8}")
