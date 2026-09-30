"""
데이터 로드 및 전처리 모듈
- 멜론 월간 차트(2015~2025) 데이터 로드
- 공백 정규화 (NBSP 등 처리)
- 해외 팝송 필터링
- 연도별 고유 곡 추출
"""

import os
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_LYRICS_CSV = PROJECT_ROOT / "private_data" / "collected" / "melon_monthly_top10_2015_2025_with_lyrics.csv"
PUBLIC_METRICS_CSV = PROJECT_ROOT / "datasets" / "lyrics_metrics.csv"

# 해외 아티스트 (순수 해외 팝송 필터링 목록)
FOREIGN_ARTISTS = [
    'Adele',
    'Ed Sheeran',
    'Camila Cabello',
    'Fitz & The Tantrums',
    'Anne-Marie',
    'Billie Eilish',
    'Naomi Scott',
    'Idina Menzel, AURORA',
    'Mariah Carey',
    'Justin Bieber',
    'The Kid LAROI, Justin Bieber',
    'GAYLE',
    'Charlie Puth',
    'LAUV',
    'Ariana Grande'
]

def load_raw_data(filepath: str = str(PRIVATE_LYRICS_CSV)) -> pd.DataFrame:
    """
    원시 CSV 데이터를 불러오고 공백 및 텍스트를 기초 정제합니다.
    """
    if not os.path.exists(filepath):
        # 상위 디렉토리에서 검색
        parent_path = os.path.join("..", filepath)
        if os.path.exists(parent_path):
            filepath = parent_path
        elif os.path.exists(PUBLIC_METRICS_CSV):
            print(f"[안내] 로컬 전용 원자료({filepath})가 없어 공개 데이터셋({PUBLIC_METRICS_CSV})을 로드합니다.")
            return load_public_metrics()
        else:
            raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {filepath}")

    df = pd.read_csv(filepath, encoding='utf-8')
    
    # 공백 문자 정규화 (\xa0 -> 일반 공백)
    if 'Title' in df.columns:
        df['Title'] = df['Title'].astype(str).str.replace('\xa0', ' ').str.strip()
    if 'Artist' in df.columns:
        df['Artist'] = df['Artist'].astype(str).str.replace('\xa0', ' ').str.strip()
    if 'Lyrics' in df.columns:
        df['Lyrics'] = df['Lyrics'].astype(str)
    
    return df

def load_public_metrics(filepath: str = str(PUBLIC_METRICS_CSV)) -> pd.DataFrame:
    """
    공개 저장소에 포함된 곡별 언어·구조 지표 데이터셋(lyrics_metrics.csv)을 로드합니다.
    (저작권 보호를 위해 원문 가사는 제외되어 있습니다)
    """
    if not os.path.exists(filepath):
        parent_path = os.path.join("..", filepath)
        if os.path.exists(parent_path):
            filepath = parent_path
        else:
            raise FileNotFoundError(f"공개 데이터셋을 찾을 수 없습니다: {filepath}")
            
    df = pd.read_csv(filepath, encoding='utf-8')
    if 'Title' in df.columns:
        df['Title'] = df['Title'].astype(str).str.replace('\xa0', ' ').str.strip()
    if 'Artist' in df.columns:
        df['Artist'] = df['Artist'].astype(str).str.replace('\xa0', ' ').str.strip()
    return df

def filter_foreign_songs(df: pd.DataFrame, exclude_foreign: bool = True):
    """
    순수 해외 팝송을 분리 및 필터링합니다.
    
    Returns:
        tuple: (국내 가요 DataFrame, 제외된 해외 팝송 DataFrame)
    """
    is_foreign = df['Artist'].isin(FOREIGN_ARTISTS)
    foreign_df = df[is_foreign].copy()
    domestic_df = df[~is_foreign].copy()
    
    if exclude_foreign:
        return domestic_df, foreign_df
    return df.copy(), foreign_df

def get_yearly_unique_songs(df: pd.DataFrame) -> pd.DataFrame:
    """
    각 연도(Year) 내에서 동일한 곡(Title, Artist)의 중복을 제거합니다.
    해당 연도에 처음 등장한 월(First Month)과 최고 순위(Peak Rank) 정보를 보존합니다.
    """
    # 이미 고유화된 데이터셋(lyrics_metrics.csv)인 경우
    if 'Month' not in df.columns and 'First_Month' in df.columns:
        return df.sort_values(by=['Year', 'First_Month', 'Peak_Rank']).reset_index(drop=True)

    agg_kwargs = {}
    if 'Month' in df.columns:
        agg_kwargs['First_Month'] = ('Month', 'min')
        agg_kwargs['Appearance_Count'] = ('Month', 'count')
    elif 'First_Month' in df.columns:
        agg_kwargs['First_Month'] = ('First_Month', 'first')

    if 'Rank' in df.columns:
        agg_kwargs['Peak_Rank'] = ('Rank', 'min')
    elif 'Peak_Rank' in df.columns:
        agg_kwargs['Peak_Rank'] = ('Peak_Rank', 'first')

    if 'Lyrics' in df.columns:
        agg_kwargs['Lyrics'] = ('Lyrics', 'first')

    # 연도별, 곡별 그룹화
    grouped = df.groupby(['Year', 'Title', 'Artist']).agg(**agg_kwargs).reset_index()
    
    # 연도 및 순위 순으로 정렬
    sort_cols = [c for c in ['Year', 'First_Month', 'Peak_Rank'] if c in grouped.columns]
    if sort_cols:
        grouped = grouped.sort_values(by=sort_cols).reset_index(drop=True)
    return grouped

def load_preprocessed_data(filepath: str = str(PRIVATE_LYRICS_CSV), 
                           exclude_foreign: bool = True,
                           yearly_unique: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    기본 분석용 전처리 완료 데이터를 로드하는 통합 함수
    
    Returns:
        tuple: (분석용 DataFrame, 제외된 해외 팝송 DataFrame)
    """
    raw_df = load_raw_data(filepath)
    domestic_df, foreign_df = filter_foreign_songs(raw_df, exclude_foreign=exclude_foreign)
    
    if yearly_unique:
        analyzed_df = get_yearly_unique_songs(domestic_df)
    else:
        analyzed_df = domestic_df
        
    return analyzed_df, foreign_df

if __name__ == "__main__":
    analyzed, foreign = load_preprocessed_data()
    print("=== 데이터 로드 및 전처리 검증 ===")
    print(f"분석 대상 연도별 고유 곡 수: {len(analyzed)}곡")
    print(f"제외된 해외 팝송 등장 건수: {len(foreign)}건 (고유곡 {len(foreign.drop_duplicates(['Title', 'Artist']))}곡)")
    print("\n[샘플 데이터 5건]")
    print(analyzed[['Year', 'First_Month', 'Peak_Rank', 'Title', 'Artist']].head())
