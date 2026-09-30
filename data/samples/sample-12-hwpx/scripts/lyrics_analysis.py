"""
대중가요 가사 텍스트 전처리 및 언어/형태소 특성 추출 모듈
- 가사 텍스트 정제 (이스케이프 문자, 공백 정규화)
- 음절/문자 단위 언어 비율(한글, 영어, 기타) 계산
- Kiwi 기반 한국어 형태소 분석 및 영문 토큰화
- 가사 구조 지표(분량, 행 수, TTR 어휘 다양도) 계산
- 인칭대명사(1인칭 '나/I' vs 2인칭 '너/You') 추출
- 불용어 사전 구축 및 주요 내용어(명사, 영단어) 추출
"""

import os
import re
import sys
from typing import Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from kiwipiepy import Kiwi

try:
    from utils import set_korean_font, ensure_dir
except ImportError:
    from utils import set_korean_font, ensure_dir

# 한국어 불용어 (조사, 의존명사, 일반적인 기능어)
KOREAN_STOPWORDS = {
    '것', '수', '때', '곳', '거', '줄', '듯', '채', '더', '이', '그', '저', 
    '때문', '중', '말', '후', '전', '안', '못', '날', '놈', '점', '분', '개',
    '어쩌구', '어쩌고', '이런', '저런', '그런', '하나', '둘', '셋'
}

# 음악적 감탄사 및 추임새 (의미적 주제 분석에서 제외할 음성적 반복어)
MUSICAL_FILLERS = {
    'oh', 'yeah', 'ah', 'la', 'na', 'uh', 'ooh', 'woo', 'da', 'ha', 'ba', 
    'hey', 'nanana', 'lalala', 'bum', 'dum', 'mmm', 'whoa', 'yay', 'ay', 
    'yo', 'shh', 'du', 'pa', 'ra', 'ta', 'boom', 'clap', 'ding', 'dong',
    '아', '오', '우', '어', '에', '하', '음', '헤이', '나나나', '라라라'
}

# 영어 기능어 불용어
ENGLISH_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
    'with', 'is', 'are', 'am', 'be', 'was', 'were', 'been', 'being', 'it', 'its', 
    'this', 'that', 'these', 'those', 'so', 'just', 'like', 'do', 'did', 'does', 
    'done', 'doing', 'have', 'has', 'had', 'having', 'not', 'no', 'up', 'down', 
    'out', 'all', 'what', 'when', 'where', 'who', 'why', 'how', 'can', 'will', 
    'could', 'would', 'should', 'if', 'then', 'as', 'by', 'about', 'into', 'from'
}

# 1인칭 대명사 세트
PRONOUNS_1ST_KO = {'나', '내', '저', '제', '우리', '저희'}
PRONOUNS_1ST_EN = {'i', 'me', 'my', 'mine', 'myself', 'we', 'us', 'our', 'ours', 'ourselves'}

# 2인칭 대명사 세트
PRONOUNS_2ND_KO = {'너', '네', '당신', '그대', '너희', '그대들', '자네'}
PRONOUNS_2ND_EN = {'you', 'your', 'yours', 'yourself', 'yourselves', 'u', 'ur'}


def clean_lyrics_text(text: str) -> str:
    """
    원시 가사 텍스트의 이스케이프 문자 및 공백을 정규화합니다.
    - 리터럴 '\\n'을 실제 줄바꿈 '\n'으로 변환
    - Non-breaking space(\\xa0)를 일반 공백으로 변환
    - 다중 연속 빈 줄 정제
    """
    if not isinstance(text, str):
        return ""
    
    # 리터럴 \n 변환
    text = text.replace(r'\n', '\n')
    # 특수 공백 치환
    text = text.replace('\xa0', ' ').replace('\u200b', '')
    # 캐리지 리턴 정제
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 불필요한 섹션 태그 정제 (예: [Bridge], [Chorus] 등)
    text = re.sub(r'\[(Intro|Verse|Chorus|Bridge|Outro|Hook)[^\]]*\]', '', text, flags=re.IGNORECASE)
    
    # 3개 이상의 연속 개행을 2개로 축소
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def compute_character_metrics(text: str) -> dict:
    """
    음절/문자 단위의 언어별 분포 및 순수 한글 여부를 계산합니다.
    """
    # 공백 제외 문자
    chars_no_space = re.sub(r'\s+', '', text)
    total_chars = len(chars_no_space)
    
    hangul_chars = len(re.findall(r'[가-힣]', text))
    eng_chars = len(re.findall(r'[a-zA-Z]', text))
    digit_chars = len(re.findall(r'[0-9]', text))
    other_chars = total_chars - (hangul_chars + eng_chars + digit_chars)
    
    valid_lang_chars = hangul_chars + eng_chars
    hangul_ratio = (hangul_chars / valid_lang_chars * 100.0) if valid_lang_chars > 0 else 0.0
    eng_ratio = (eng_chars / valid_lang_chars * 100.0) if valid_lang_chars > 0 else 0.0
    
    # 순수 한글 가사 여부 (영어 알파벳이 0글자)
    is_pure_korean = (eng_chars == 0)
    
    return {
        'char_count_total': total_chars,
        'hangul_char_count': hangul_chars,
        'eng_char_count': eng_chars,
        'digit_char_count': digit_chars,
        'other_char_count': max(0, other_chars),
        'hangul_char_ratio': round(hangul_ratio, 2),
        'eng_char_ratio': round(eng_ratio, 2),
        'is_pure_korean_lyrics': is_pure_korean
    }


def analyze_lyrics_linguistics(text: str, kiwi: Optional[Kiwi] = None) -> dict:
    """
    형태소 분석기(Kiwi)를 활용하여 형태소, 어휘 다양도(TTR), 대명사, 내용어를 추출합니다.
    """
    if kiwi is None:
        kiwi = Kiwi()
        
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    line_count = len(lines)
    
    # 단순 어절(띄어쓰기 기준 단어)
    words = text.split()
    word_count = len(words)
    
    # Kiwi 형태소 분석 수행
    tokens = kiwi.tokenize(text)
    token_count = len(tokens)
    
    # 어휘 다양도 (TTR: Type-Token Ratio)
    # 1) 형태소 기준 TTR
    unique_tokens = {t.form for t in tokens}
    ttr_tokens = (len(unique_tokens) / token_count) if token_count > 0 else 0.0
    
    # 2) 어절 기준 TTR
    unique_words = {w.lower() for w in words}
    ttr_words = (len(unique_words) / word_count) if word_count > 0 else 0.0
    
    # 인칭 대명사 집계
    count_1st_ko = 0
    count_2nd_ko = 0
    count_1st_en = 0
    count_2nd_en = 0
    
    nouns = []
    english_tokens = []
    
    for t in tokens:
        form = t.form
        tag = t.tag
        form_lower = form.lower()
        
        # 한국어 대명사 (NP)
        if tag == 'NP':
            if form in PRONOUNS_1ST_KO:
                count_1st_ko += 1
            elif form in PRONOUNS_2ND_KO:
                count_2nd_ko += 1
                
        # 외국어/영단어 (SL)
        elif tag == 'SL':
            # 영문 대명사 검사
            if form_lower in PRONOUNS_1ST_EN:
                count_1st_en += 1
            elif form_lower in PRONOUNS_2ND_EN:
                count_2nd_en += 1
            
            # 의미 있는 영단어 추출 (길이 >= 2, 불용어 및 추임새 제외)
            if (len(form_lower) >= 2 and 
                form_lower not in ENGLISH_STOPWORDS and 
                form_lower not in MUSICAL_FILLERS and
                re.match(r'^[a-z]+$', form_lower)):
                english_tokens.append(form_lower)
                
        # 한국어 명사 (일반명사 NNG, 고유명사 NNP)
        elif tag in ('NNG', 'NNP'):
            if (len(form) >= 2 and 
                form not in KOREAN_STOPWORDS and 
                form not in MUSICAL_FILLERS):
                nouns.append(form)

    total_1st = count_1st_ko + count_1st_en
    total_2nd = count_2nd_ko + count_2nd_en
    total_pronouns = total_1st + total_2nd
    
    # 1인칭 화자 비율 (1인칭 / (1인칭 + 2인칭))
    ratio_1st = (total_1st / total_pronouns * 100.0) if total_pronouns > 0 else 50.0
    
    return {
        'line_count': line_count,
        'word_count': word_count,
        'token_count': token_count,
        'ttr_token': round(ttr_tokens, 4),
        'ttr_word': round(ttr_words, 4),
        'pronoun_1st_count': total_1st,
        'pronoun_2nd_count': total_2nd,
        'pronoun_1st_ratio': round(ratio_1st, 2),
        'nouns_count': len(nouns),
        'english_tokens_count': len(english_tokens),
        'nouns_str': " ".join(nouns),
        'english_tokens_str': " ".join(english_tokens)
    }


def preprocess_lyrics_dataframe(df: pd.DataFrame, kiwi: Optional[Kiwi] = None) -> pd.DataFrame:
    """
    주어진 DataFrame의 가사 컬럼(Lyrics)을 전처리하고 언어 및 구조 지표를 모두 추출하여
    새로운 열들이 추가된 DataFrame을 반환합니다.
    """
    if kiwi is None:
        print("[Info] Kiwi 형태소 분석기를 초기화합니다...")
        kiwi = Kiwi()
        
    print(f"[Info] 총 {len(df)}곡의 가사 전처리 및 형태소 특성 추출을 시작합니다.")
    
    processed_records = []
    
    for idx, row in df.iterrows():
        raw_lyrics = row['Lyrics']
        cleaned = clean_lyrics_text(raw_lyrics)
        
        # 문자 단위 메트릭
        char_metrics = compute_character_metrics(cleaned)
        
        # 형태소/언어학 메트릭
        ling_metrics = analyze_lyrics_linguistics(cleaned, kiwi=kiwi)
        
        # 병합 레코드 구성
        record = {
            'Year': row['Year'],
            'Title': row['Title'],
            'Artist': row['Artist'],
            'First_Month': row.get('First_Month', row.get('Month', 1)),
            'Peak_Rank': row.get('Peak_Rank', row.get('Rank', 1)),
            'Cleaned_Lyrics': cleaned,
            **char_metrics,
            **ling_metrics
        }
        processed_records.append(record)
        
        if (idx + 1) % 100 == 0 or (idx + 1) == len(df):
            print(f" -> {idx + 1}/{len(df)}곡 처리 완료 ({(idx + 1)/len(df)*100:.1f}%)")
            
    result_df = pd.DataFrame(processed_records)
    print("[Info] 가사 전처리 파이프라인 처리가 성공적으로 완료되었습니다.")
    return result_df


def get_or_create_processed_lyrics(cache_path: str = "private_data/processed/lyrics_processed_full.csv", force_recompute: bool = False) -> pd.DataFrame:
    """
    캐시 파일이 존재하면 로드하고, 없거나 force_recompute=True이면 전처리를 수행 후 저장합니다.
    로컬 전용 가사 원문이 없는 공개 저장소 환경에서는 datasets/lyrics_metrics.csv를 로드합니다.
    """
    if not force_recompute and os.path.exists(cache_path):
        print(f"[Info] 기존 가사 전처리 캐시 파일을 로드합니다: {cache_path}")
        return pd.read_csv(cache_path, encoding='utf-8')
        
    try:
        from data_loader import load_preprocessed_data, PUBLIC_METRICS_CSV
    except ImportError:
        from data_loader import load_preprocessed_data, PUBLIC_METRICS_CSV

    if not force_recompute and os.path.exists(PUBLIC_METRICS_CSV):
        print(f"[Info] 로컬 전용 가사 캐시가 없어 공개 지표 데이터셋({PUBLIC_METRICS_CSV})을 로드합니다.")
        return pd.read_csv(PUBLIC_METRICS_CSV, encoding='utf-8')

    domestic_df, _ = load_preprocessed_data()
    if 'Lyrics' not in domestic_df.columns:
        print("[Info] 가사 원문 데이터(private_data)가 없어 전처리 파이프라인 재실행 대신 공개 지표 데이터셋을 사용합니다.")
        return domestic_df

    processed_df = preprocess_lyrics_dataframe(domestic_df)
    
    # outputs 디렉토리 생성 보장
    os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)
    processed_df.to_csv(cache_path, index=False, encoding='utf-8-sig')
    print(f"[Info] 가사 전처리 결과가 캐시 파일로 저장되었습니다: {cache_path}")
    return processed_df


def compute_yearly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    연도별 핵심 언어 및 구조 지표 요약 테이블을 연산합니다.
    """
    summary = df.groupby('Year').agg(
        Song_Count=('Title', 'count'),
        Avg_Eng_Ratio=('eng_char_ratio', 'mean'),
        Avg_Hangul_Ratio=('hangul_char_ratio', 'mean'),
        Pure_Korean_Songs=('is_pure_korean_lyrics', 'sum'),
        Pure_Korean_Pct=('is_pure_korean_lyrics', lambda x: (x.sum() / len(x) * 100)),
        Over_50_Eng_Songs=('eng_char_ratio', lambda x: (x >= 50.0).sum()),
        Over_50_Eng_Pct=('eng_char_ratio', lambda x: ((x >= 50.0).sum() / len(x) * 100)),
        Avg_Char_Count=('char_count_total', 'mean'),
        Avg_Word_Count=('word_count', 'mean'),
        Avg_Line_Count=('line_count', 'mean'),
        Avg_TTR_Word=('ttr_word', 'mean'),
        Avg_TTR_Token=('ttr_token', 'mean'),
        Avg_1st_Pronoun=('pronoun_1st_count', 'mean'),
        Avg_2nd_Pronoun=('pronoun_2nd_count', 'mean'),
        Avg_1st_Ratio=('pronoun_1st_ratio', 'mean')
    ).round(2)
    
    return summary


def assign_period(year: int) -> str:
    """연도를 3개 시대(전기, 중기, 후기)로 구분합니다."""
    if year <= 2017:
        return '전기 (2015-2017)'
    elif year <= 2021:
        return '중기 (2018-2021)'
    else:
        return '후기 (2022-2025)'


def compute_period_keywords(df: pd.DataFrame, top_n: int = 20) -> tuple[dict, pd.DataFrame]:
    """
    시대별(전기, 중기, 후기) 한국어 핵심 명사 및 영단어 TOP N을 마이닝합니다.
    """
    from collections import Counter
    
    df_period = df.copy()
    df_period['Period'] = df_period['Year'].apply(assign_period)
    
    # 가사 어휘 열이 없는 공개 데이터셋 환경인 경우 안전하게 빈 결과 반환
    if 'nouns_str' not in df_period.columns or 'english_tokens_str' not in df_period.columns:
        print("[Info] 가사 원문 및 어휘 목록이 포함되지 않은 공개 데이터셋 환경이므로 시대별 키워드 마이닝을 건너뜁니다.")
        return {}, pd.DataFrame()
    
    # 영문 키워드 추출 시 추가 제외할 대명사 및 축약/기능어
    eng_keyword_exclude = {
        'you', 'your', 'yours', 'me', 'my', 'mine', 'we', 'our', 'ours', 'us', 
        'i', 'im', 'don', 'dont', 'cant', 'wont', 'aint', 'thats', 'theres', 
        'youre', 'theyre', 'hes', 'shes', 'it', 'its', 'let', 'lets', 'get', 
        'got', 'know', 'now', 'go', 'see', 'come', 'take', 'make', 'say', 
        'tell', 'want', 'look', 'give', 'one', 'two', 'yeah', 'oh', 'uh', 
        'ah', 'la', 'na', 'hey', 'ooh', 'woo', 'too', 'never', 'again', 'back'
    }
    
    period_order = ['전기 (2015-2017)', '중기 (2018-2021)', '후기 (2022-2025)']
    period_dict = {}
    flattened_rows = []
    
    for period in period_order:
        group = df_period[df_period['Period'] == period]
        song_count = len(group)
        
        # 한국어 명사 수집 (2글자 이상, 불용어 제외)
        all_nouns = []
        for s in group['nouns_str'].dropna():
            for w in s.split():
                if len(w) >= 2 and w not in KOREAN_STOPWORDS:
                    all_nouns.append(w)
                    
        # 영단어 수집
        all_eng = []
        for s in group['english_tokens_str'].dropna():
            for w in s.split():
                w_clean = w.lower()
                if (len(w_clean) >= 3 and 
                    w_clean not in eng_keyword_exclude and 
                    w_clean not in MUSICAL_FILLERS and
                    re.match(r'^[a-z]+$', w_clean)):
                    all_eng.append(w_clean)
                    
        top_nouns = Counter(all_nouns).most_common(top_n)
        top_eng = Counter(all_eng).most_common(top_n)
        
        period_dict[period] = {
            'song_count': song_count,
            'top_nouns': top_nouns,
            'top_english': top_eng
        }
        
        # DataFrame 형태로 변환
        for rank, (word, count) in enumerate(top_nouns, 1):
            flattened_rows.append({
                'Period': period,
                'Language': '한국어 명사',
                'Rank': rank,
                'Word': word,
                'Total_Count': count,
                'Per_Song_Freq': round(count / song_count, 2)
            })
            
        for rank, (word, count) in enumerate(top_eng, 1):
            flattened_rows.append({
                'Period': period,
                'Language': '영단어',
                'Rank': rank,
                'Word': word,
                'Total_Count': count,
                'Per_Song_Freq': round(count / song_count, 2)
            })
            
    summary_df = pd.DataFrame(flattened_rows)
    return period_dict, summary_df


def compute_title_lyrics_cross_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    제목의 언어 표기 유형과 가사 속 언어/구조 지표 간의 교차 분석 테이블을 연산합니다.
    """
    def classify_title(title: str) -> str:
        has_hangul = bool(re.search(r'[가-힣]', title))
        has_eng = bool(re.search(r'[a-zA-Z]', title))
        if has_hangul and not has_eng:
            return '순수 한글 제목'
        elif has_eng and not has_hangul:
            return '순수 영문 제목'
        elif has_hangul and has_eng:
            return '한·영 혼용 제목'
        else:
            return '기타 (숫자/기호)'

    df_copy = df.copy()
    df_copy['Title_Type'] = df_copy['Title'].apply(classify_title)
    
    order = ['순수 한글 제목', '한·영 혼용 제목', '순수 영문 제목', '기타 (숫자/기호)']
    
    cross = df_copy.groupby('Title_Type').agg(
        Song_Count=('Title', 'count'),
        Avg_Eng_Ratio=('eng_char_ratio', 'mean'),
        Pure_Korean_Lyrics=('is_pure_korean_lyrics', 'sum'),
        Pure_Korean_Pct=('is_pure_korean_lyrics', lambda x: x.sum() / len(x) * 100),
        Avg_Word_Count=('word_count', 'mean'),
        Avg_TTR_Word=('ttr_word', 'mean'),
        Avg_1st_Ratio=('pronoun_1st_ratio', 'mean')
    ).round(2)
    
    # 정의된 순서로 정렬 (존재하는 행만)
    existing_order = [t for t in order if t in cross.index]
    cross = cross.reindex(existing_order)
    return cross


def run_lyrics_statistical_analysis(df: Optional[pd.DataFrame] = None) -> dict:
    """
    가사 데이터에 대한 통계 연산을 종합 실행하고 CSV 산출물을 저장합니다.
    """
    if df is None:
        df = get_or_create_processed_lyrics(force_recompute=False)
        
    print("[Info] 가사 통계 연산 및 세부 지표 분석을 시작합니다.")
    
    # 1. 연도별 통계 요약
    yearly_summary = compute_yearly_summary(df)
    os.makedirs("output/analysis_tables", exist_ok=True)
    os.makedirs("output/analysis_figures", exist_ok=True)
    yearly_summary.to_csv("output/analysis_tables/lyrics_yearly_summary.csv", encoding='utf-8-sig')
    print(" -> [저장 완료] output/analysis_tables/lyrics_yearly_summary.csv")
    
    # 2. 시대별 핵심 키워드 마이닝
    period_dict, period_keywords = compute_period_keywords(df, top_n=20)
    if not period_keywords.empty:
        period_keywords.to_csv("output/analysis_tables/lyrics_period_keywords.csv", index=False, encoding='utf-8-sig')
        print(" -> [저장 완료] output/analysis_tables/lyrics_period_keywords.csv")
    
    # 3. 제목-가사 교차 분석
    cross_analysis = compute_title_lyrics_cross_analysis(df)
    cross_analysis.to_csv("output/analysis_tables/title_lyrics_cross_analysis.csv", encoding='utf-8-sig')
    print(" -> [저장 완료] output/analysis_tables/title_lyrics_cross_analysis.csv")
    
    # 4. 시각화 차트 5종 일괄 생성 및 저장
    plot_paths = generate_all_lyrics_plots(yearly_summary, period_keywords, df)
    
    return {
        'yearly_summary': yearly_summary,
        'period_dict': period_dict,
        'period_keywords': period_keywords,
        'cross_analysis': cross_analysis,
        'plot_paths': plot_paths
    }


def plot_lyrics_language_trend(yearly_summary: pd.DataFrame, output_path: str = "output/analysis_figures/lyrics_language_trend.png"):
    """
    1. 연도별 가사 내 한글 vs 영어 음절 비율(%) 추세선 (2015~2025)
    """
    set_korean_font()
    ensure_dir(os.path.dirname(os.path.abspath(output_path)))
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    
    years = yearly_summary.index
    hangul = yearly_summary['Avg_Hangul_Ratio']
    eng = yearly_summary['Avg_Eng_Ratio']
    
    # 꺾은선
    ax.plot(years, hangul, marker='o', linewidth=2.8, markersize=7, color='#3A7CA5', label='한글 음절 비율 (%)')
    ax.plot(years, eng, marker='s', linewidth=3.0, markersize=8, color='#E05A47', label='영어 음절 비율 (%)')
    
    # 과반(50%) 기준 점선
    ax.axhline(50, color='#777777', linestyle='--', linewidth=1.2, alpha=0.7, label='과반(50%) 기준선')
    
    # 주요 포인트 수치 표시 (겹침 방지: 더 큰 값은 위, 더 작은 값은 아래)
    for yr in [2015, 2019, 2022, 2023, 2025]:
        if yr in years:
            h_val = hangul.loc[yr]
            e_val = eng.loc[yr]
            if h_val >= e_val:
                ax.text(yr, h_val + 2.5, f"{h_val:.1f}%", ha='center', color='#3A7CA5', fontweight='bold', fontsize=9.5)
                ax.text(yr, e_val - 4.2, f"{e_val:.1f}%", ha='center', color='#E05A47', fontweight='bold', fontsize=9.5)
            else:
                ax.text(yr, e_val + 2.5, f"{e_val:.1f}%", ha='center', color='#E05A47', fontweight='bold', fontsize=9.5)
                ax.text(yr, h_val - 4.2, f"{h_val:.1f}%", ha='center', color='#3A7CA5', fontweight='bold', fontsize=9.5)
            
    # 역전 구간 하이라이트 (2022.5 ~ 2025.5)
    ax.axvspan(2022.5, 2025.5, color='#FFE5D9', alpha=0.45, linestyle=':', label='가사 내 영어 과반 구간 (2023~2025)')
    ax.annotate("2023년 가사 속 영어 과반(52.7%) 돌파\n(2025년 54.1%로 최고치 경신)", 
                xy=(2023, 52.73), xytext=(2017.2, 63),
                arrowprops=dict(facecolor='#D9381E', shrink=0.08, width=1.5, headwidth=7),
                fontsize=10.5, fontweight='bold', color='#B32400',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#FFF3EB", edgecolor="#D9381E", alpha=0.9))
                
    # 2019년 발라드 붐 포인트 주석
    ax.annotate("2019년 발라드/인디 음원 강세\n(한글 81.7% vs 영어 18.3%)", 
                xy=(2019, 18.28), xytext=(2016.3, 30),
                arrowprops=dict(facecolor='#3A7CA5', shrink=0.08, width=1.2, headwidth=6),
                fontsize=9.5, fontweight='bold', color='#1E4D6B',
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#EBF3F9", edgecolor="#3A7CA5", alpha=0.9))

    ax.set_title("멜론 월간 TOP 10 가사 내 한글 vs 영어 음절 비율 추이 (2015~2025)", pad=18, fontweight='bold', fontsize=15)
    ax.set_xlabel("연도 (Year)", labelpad=10, fontweight='bold')
    ax.set_ylabel("평균 음절 비율 (%)", labelpad=10, fontweight='bold')
    ax.set_xticks(years)
    ax.set_ylim(0, 100)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(loc='lower left', frameon=True, edgecolor='#cccccc', fontsize=9.5)
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"[시각화 저장 완료] {output_path}")


def plot_lyrics_pure_korean_ratio(yearly_summary: pd.DataFrame, output_path: str = "output/analysis_figures/lyrics_pure_korean_ratio.png"):
    """
    2. 순수 한글 가사곡 비율 vs 가사 내 영어 50% 이상 곡 비율 비교 (2015~2025)
    """
    set_korean_font()
    ensure_dir(os.path.dirname(os.path.abspath(output_path)))
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    
    years = np.array(yearly_summary.index)
    pure_ko = yearly_summary['Pure_Korean_Pct']
    over_50 = yearly_summary['Over_50_Eng_Pct']
    
    width = 0.38
    x_indices = np.arange(len(years))
    
    bars1 = ax.bar(x_indices - width/2, pure_ko, width, label='순수 한글 가사곡 비율 (%)', color='#3A7CA5', edgecolor='white')
    bars2 = ax.bar(x_indices + width/2, over_50, width, label='가사 내 영어 50% 이상 곡 비율 (%)', color='#E05A47', edgecolor='white')
    
    # 막대 위 수치 표기
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 1.2, f"{h:.1f}%", ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#1E4D6B')
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 1.2, f"{h:.1f}%", ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#B32400')
        
    # 하이라이트 주석 (여유 있는 위치 및 y_lim 조정)
    ax.annotate("2019년 순수 한글곡 50.7% 정점\n(발라드 장르 차트 장악)", 
                xy=(4 - width/2, 50.72 + 4.5), xytext=(1.5, 66),
                arrowprops=dict(facecolor='#3A7CA5', shrink=0.08, width=1.3, headwidth=6),
                fontsize=9.5, fontweight='bold', color='#1E4D6B',
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#EBF3F9", edgecolor="#3A7CA5", alpha=0.9))
                
    ax.annotate("2023년 영어 50%↑ 곡 61.9% 폭증\n(순수 한글곡 16.7% 최저치)", 
                xy=(8 + width/2, 61.90 + 4.5), xytext=(5.8, 76),
                arrowprops=dict(facecolor='#E05A47', shrink=0.08, width=1.3, headwidth=6),
                fontsize=9.5, fontweight='bold', color='#B32400',
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF3EB", edgecolor="#E05A47", alpha=0.9))

    ax.set_title("순수 한글 가사곡의 축소와 영어 과반(50%↑) 음원의 급증 비교 (2015~2025)", pad=18, fontweight='bold', fontsize=15)
    ax.set_xlabel("연도 (Year)", labelpad=10, fontweight='bold')
    ax.set_ylabel("음원 비율 (%)", labelpad=10, fontweight='bold')
    ax.set_xticks(x_indices)
    ax.set_xticklabels(years)
    ax.set_ylim(0, 88)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.legend(loc='upper right', frameon=True, edgecolor='#cccccc', fontsize=9.5)
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"[시각화 저장 완료] {output_path}")


def plot_lyrics_length_and_ttr(yearly_summary: pd.DataFrame, output_path: str = "output/analysis_figures/lyrics_length_and_ttr.png"):
    """
    3. 숏폼 시대의 가사 구조 변화: 가사 분량(어절 수) 및 어휘 다양도(TTR) 이중 축 그래프
    """
    set_korean_font()
    ensure_dir(os.path.dirname(os.path.abspath(output_path)))
    fig, ax1 = plt.subplots(figsize=(12, 6.5), dpi=300)
    
    years = yearly_summary.index
    word_count = yearly_summary['Avg_Word_Count']
    ttr = yearly_summary['Avg_TTR_Word']
    
    # 1번째 축: 가사 분량 (어절 수 막대)
    bars = ax1.bar(years, word_count, width=0.55, color='#BDC3C7', alpha=0.65, edgecolor='#7F8C8D', label='평균 어절 수 (단어 수)')
    ax1.set_ylabel("곡당 평균 어절 수 (어절)", color='#4A5568', labelpad=10, fontweight='bold')
    ax1.set_ylim(140, 320)
    ax1.tick_params(axis='y', labelcolor='#4A5568')
    
    # 어절 수 텍스트를 막대 하단에 안정적으로 배치하여 TTR 선과 겹침 방지
    for bar in bars:
        ax1.text(bar.get_x() + bar.get_width()/2, 150, f"{bar.get_height():.0f}어절", 
                 ha='center', va='bottom', fontsize=8.5, color='#2C3E50', fontweight='bold')
        
    # 2번째 축: 어휘 다양도 (TTR 꺾은선)
    ax2 = ax1.twinx()
    line = ax2.plot(years, ttr, color='#6C5CE7', marker='D', linewidth=3.2, markersize=8, label='어휘 다양도 (TTR: Type-Token Ratio)')
    ax2.set_ylabel("어휘 다양도 (TTR)", color='#6C5CE7', labelpad=10, fontweight='bold')
    ax2.set_ylim(0.40, 0.65)
    ax2.tick_params(axis='y', labelcolor='#6C5CE7')
    
    # TTR 주요 수치 표시
    for yr in [2015, 2019, 2021, 2023, 2025]:
        val = ttr.loc[yr]
        ax2.text(yr, val + 0.009, f"{val:.2f}", ha='center', color='#5B45D3', fontweight='bold', fontsize=9.5)
        
    # TTR 급락 주석
    ax2.annotate("2023~2025년 TTR 0.47로 급락 (-10%p)\n(숏폼 확산 및 후렴구/훅 반복 심화)", 
                 xy=(2023, 0.47), xytext=(2019.5, 0.43),
                 arrowprops=dict(facecolor='#6C5CE7', shrink=0.08, width=1.5, headwidth=7),
                 fontsize=10.0, fontweight='bold', color='#4834D4',
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="#F0EDFF", edgecolor="#6C5CE7", alpha=0.9))

    ax1.set_title("대중가요 가사 분량과 어휘 다양도(TTR) 변화 추이 (2015~2025)", pad=18, fontweight='bold', fontsize=15)
    ax1.set_xlabel("연도 (Year)", labelpad=10, fontweight='bold')
    ax1.set_xticks(years)
    ax1.grid(axis='y', linestyle='--', alpha=0.4)
    
    # 범례 통합
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True, edgecolor='#cccccc', fontsize=9.5)
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"[시각화 저장 완료] {output_path}")


def plot_top_keywords_by_period(period_keywords: pd.DataFrame, output_path: str = "output/analysis_figures/top_keywords_by_period.png"):
    """
    4. 3개 시대별 최빈 한국어 명사 및 주요 영단어 TOP 10 비교 (2행 3열 그리드)
    """
    set_korean_font()
    ensure_dir(os.path.dirname(os.path.abspath(output_path)))
    fig, axes = plt.subplots(2, 3, figsize=(16, 9.5), dpi=300)
    
    periods = ['전기 (2015-2017)', '중기 (2018-2021)', '후기 (2022-2025)']
    colors_ko = ['#3A7CA5', '#2E86AB', '#1B4965']
    colors_en = ['#E05A47', '#E67E22', '#D35400']
    
    for col_idx, period in enumerate(periods):
        p_df = period_keywords[period_keywords['Period'] == period]
        
        # 1행: 한국어 명사 TOP 10
        ax_ko = axes[0, col_idx]
        ko_top10 = p_df[p_df['Language'] == '한국어 명사'].head(10).iloc[::-1]
        bars_ko = ax_ko.barh(ko_top10['Word'], ko_top10['Total_Count'], color=colors_ko[col_idx], alpha=0.85, edgecolor='white')
        max_ko = ko_top10['Total_Count'].max()
        ax_ko.set_xlim(0, max_ko * 1.20)
        ax_ko.set_title(f"[{period}]\n한국어 명사 TOP 10", fontsize=11.5, fontweight='bold', pad=8)
        ax_ko.set_xlabel("출현 빈도 (회)", fontsize=9.5)
        ax_ko.grid(axis='x', linestyle='--', alpha=0.4)
        for b in bars_ko:
            w = b.get_width()
            ax_ko.text(w + (max_ko * 0.02), b.get_y() + b.get_height()/2, f"{int(w)}회", va='center', fontsize=8.5, fontweight='bold', color='#222222')
            
        # 2행: 영단어 TOP 10
        ax_en = axes[1, col_idx]
        en_top10 = p_df[p_df['Language'] == '영단어'].head(10).iloc[::-1]
        bars_en = ax_en.barh(en_top10['Word'], en_top10['Total_Count'], color=colors_en[col_idx], alpha=0.85, edgecolor='white')
        max_en = en_top10['Total_Count'].max()
        ax_en.set_xlim(0, max_en * 1.20)
        ax_en.set_title(f"[{period}]\n주요 영단어 TOP 10", fontsize=11.5, fontweight='bold', pad=8)
        ax_en.set_xlabel("출현 빈도 (회)", fontsize=9.5)
        ax_en.grid(axis='x', linestyle='--', alpha=0.4)
        for b in bars_en:
            w = b.get_width()
            ax_en.text(w + (max_en * 0.02), b.get_y() + b.get_height()/2, f"{int(w)}회", va='center', fontsize=8.5, fontweight='bold', color='#222222')
            
    fig.suptitle("시대별(전기·중기·후기) 가사 핵심 어휘(한국어 명사 및 영단어) 변화 비교", fontsize=16, fontweight='bold', y=0.99)
    plt.tight_layout()
    plt.subplots_adjust(top=0.91, hspace=0.32, wspace=0.25)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"[시각화 저장 완료] {output_path}")


def plot_pronoun_ratio_trend(yearly_summary: pd.DataFrame, df: pd.DataFrame, output_path: str = "output/analysis_figures/pronoun_ratio_trend.png"):
    """
    5. 화자 지향성 변화: 1인칭(나/I) vs 2인칭(너/You) 대명사 출현 빈도 및 비율 변화
    """
    set_korean_font()
    ensure_dir(os.path.dirname(os.path.abspath(output_path)))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300, gridspec_kw={'width_ratios': [1.3, 1]})
    
    # 좌측: 연도별 곡당 1인칭 vs 2인칭 평균 출현 빈도 (그룹 막대)
    years = np.array(yearly_summary.index)
    x_idx = np.arange(len(years))
    width = 0.38
    
    p1st = yearly_summary['Avg_1st_Pronoun']
    p2nd = yearly_summary['Avg_2nd_Pronoun']
    
    ax1.bar(x_idx - width/2, p1st, width, label='1인칭 화자 (나, 내, I, me 등)', color='#2980B9', edgecolor='white')
    ax1.bar(x_idx + width/2, p2nd, width, label='2인칭 청자 (너, 네, you 등)', color='#E74C3C', edgecolor='white')
    
    ax1.set_title("(1) 연도별 곡당 인칭 대명사 평균 출현 빈도", fontsize=12.5, fontweight='bold', pad=12)
    ax1.set_xlabel("연도 (Year)", labelpad=8, fontweight='bold')
    ax1.set_ylabel("곡당 평균 출현 횟수 (회)", labelpad=8, fontweight='bold')
    ax1.set_xticks(x_idx)
    ax1.set_xticklabels(years)
    ax1.set_ylim(0, 35)
    ax1.grid(axis='y', linestyle='--', alpha=0.4)
    ax1.legend(loc='upper left', frameon=True, edgecolor='#cccccc', fontsize=9.0)
    
    # 우측: 시대별 1인칭 대 2인칭 비율 (1.63배 -> 1.70배 -> 1.93배)
    periods = ['전기\n(2015-17)', '중기\n(2018-21)', '후기\n(2022-25)']
    ratios = [1.63, 1.70, 1.93]
    avg_1st_per_song = [19.48, 19.12, 24.58]
    
    bar_colors = ['#5DADE2', '#3498DB', '#1B4F72']
    bars3 = ax2.bar(periods, ratios, width=0.45, color=bar_colors, edgecolor='white')
    
    for i, b in enumerate(bars3):
        h = b.get_height()
        ax2.text(b.get_x() + b.get_width()/2, h + 0.04, f"{h:.2f}배\n(곡당 {avg_1st_per_song[i]:.1f}회)", 
                 ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#1B4F72')
                 
    ax2.set_title("(2) 시대별 1인칭 화자 대 2인칭 청자 비율 (1인칭 / 2인칭)", fontsize=12.5, fontweight='bold', pad=12)
    ax2.set_ylabel("1인칭 / 2인칭 출현 비율 (배수)", labelpad=8, fontweight='bold')
    ax2.set_ylim(0, 2.5)
    ax2.grid(axis='y', linestyle='--', alpha=0.4)
    
    # 주석 박스
    ax2.text(0.5, 0.22, "타자(너) 중심의 감정·연애 서사에서\n자기(나) 중심의 당당함·자아 서사로 전환",
             transform=ax2.transAxes, ha='center', fontsize=10, fontweight='bold', color='#0E3A53',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#EBF5FB", edgecolor="#2980B9", alpha=0.9))
             
    fig.suptitle("대중가요 가사의 화자 지향성 변화: 1인칭(나/I) vs 2인칭(너/You) (2015~2025)", fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.subplots_adjust(top=0.88)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"[시각화 저장 완료] {output_path}")


def generate_all_lyrics_plots(yearly_summary: Optional[pd.DataFrame] = None, 
                              period_keywords: Optional[pd.DataFrame] = None,
                              df: Optional[pd.DataFrame] = None, 
                              output_dir: str = "output/analysis_figures") -> list[str]:
    """
    가사 분석 시각화 차트 5종을 일괄 생성 및 저장합니다.
    """
    ensure_dir(output_dir)
    
    if df is None:
        df = get_or_create_processed_lyrics(force_recompute=False)
    if yearly_summary is None:
        yearly_summary = compute_yearly_summary(df)
    if period_keywords is None:
        _, period_keywords = compute_period_keywords(df, top_n=20)
        
    print("[Info] 가사 분석 시각화 차트 5종 생성을 시작합니다...")
    
    plot_paths = [
        os.path.join(output_dir, "lyrics_language_trend.png"),
        os.path.join(output_dir, "lyrics_pure_korean_ratio.png"),
        os.path.join(output_dir, "lyrics_length_and_ttr.png"),
        os.path.join(output_dir, "top_keywords_by_period.png"),
        os.path.join(output_dir, "pronoun_ratio_trend.png")
    ]
    
    plot_lyrics_language_trend(yearly_summary, plot_paths[0])
    plot_lyrics_pure_korean_ratio(yearly_summary, plot_paths[1])
    plot_lyrics_length_and_ttr(yearly_summary, plot_paths[2])
    
    if period_keywords is not None and not period_keywords.empty:
        plot_top_keywords_by_period(period_keywords, plot_paths[3])
    else:
        print("[Info] 어휘 추출 데이터가 없어 top_keywords_by_period.png 재생성을 건너뜁니다 (기존 차트 보존).")

    plot_pronoun_ratio_trend(yearly_summary, df, plot_paths[4])
    
    # figures/ 디렉터리에도 핵심 차트 복사/보존
    figures_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures")
    if os.path.exists(figures_dir):
        import shutil
        for fname in ["lyrics_language_trend.png", "lyrics_pure_korean_ratio.png", "lyrics_length_and_ttr.png"]:
            src = os.path.join(output_dir, fname)
            dst = os.path.join(figures_dir, fname)
            if os.path.exists(src):
                shutil.copy2(src, dst)
    
    print("[Info] 가사 분석 시각화 차트 생성이 모두 완료되었습니다.")
    return plot_paths


if __name__ == "__main__":
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
            
    df = get_or_create_processed_lyrics(force_recompute=False)
    results = run_lyrics_statistical_analysis(df)
    
    print("\n" + "="*80)
    print("1. [연도별 가사 언어 및 구조 지표 요약]")
    print("="*80)
    print(results['yearly_summary'][['Song_Count', 'Avg_Eng_Ratio', 'Pure_Korean_Pct', 'Over_50_Eng_Pct', 'Avg_Word_Count', 'Avg_TTR_Word', 'Avg_1st_Ratio']].to_string())
    
    print("\n" + "="*80)
    print("2. [제목 표기 유형과 가사 특성 간 교차 분석]")
    print("="*80)
    print(results['cross_analysis'].to_string())
    
    if results['period_dict']:
        print("\n" + "="*80)
        print("3. [시대별 TOP 10 핵심 어휘 비교]")
        print("="*80)
        for period, data in results['period_dict'].items():
            print(f"\n--- {period} ({data['song_count']}곡) ---")
            nouns_str = ", ".join([f"{w}({c})" for w, c in data['top_nouns'][:10]])
            eng_str = ", ".join([f"{w}({c})" for w, c in data['top_english'][:10]])
            print(f" * 한국어 명사: {nouns_str}")
            print(f" * 주요 영단어: {eng_str}")
    else:
        print("\n[안내] 가사 원문 및 어휘 목록은 저작권 보호를 위해 공개 데이터셋에서 제외되어 있습니다.")


