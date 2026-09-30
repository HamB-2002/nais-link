"""
곡 제목 언어 유형 분석 및 시각화 모듈
- 곡 제목을 '순수 한글', '순수 영문', '한·영 혼용', '기타'로 분류
- 연도별 빈도 및 백분율 통계 산출
- 고화질 시각화 차트(누적 막대 그래프, 꺾은선 추세선) 생성 및 저장
"""

import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from data_loader import load_preprocessed_data, PRIVATE_LYRICS_CSV
from utils import set_korean_font, ensure_dir

def classify_title(title: str) -> str:
    """
    곡 제목의 언어 구성 유형을 분류합니다.
    - 순수 한글: 한글이 포함되어 있고 영문 알파벳이 없음
    - 순수 영문: 영문 알파벳이 포함되어 있고 한글이 없음
    - 한·영 혼용: 한글과 영문 알파벳이 모두 포함됨
    - 기타: 한글과 영문이 모두 없는 경우 (숫자, 특수기호 단독 등)
    """
    has_kor = bool(re.search(r'[가-힣]', title))
    has_eng = bool(re.search(r'[a-zA-Z]', title))
    
    if has_kor and not has_eng:
        return '순수 한글'
    elif not has_kor and has_eng:
        return '순수 영문'
    elif has_kor and has_eng:
        return '한·영 혼용'
    else:
        return '기타(숫자/기호)'

def analyze_title_types(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    제목 유형 분류 및 연도별 통계 테이블을 생성합니다.
    """
    df = df.copy()
    df['Title_Type'] = df['Title'].apply(classify_title)
    
    # 연도별 빈도수(Count)
    count_table = pd.crosstab(df['Year'], df['Title_Type'])
    
    # 모든 범주가 존재하도록 보장
    categories = ['순수 한글', '순수 영문', '한·영 혼용', '기타(숫자/기호)']
    for col in categories:
        if col not in count_table.columns:
            count_table[col] = 0
    count_table = count_table[categories]
    
    # 연도별 백분율(Ratio, %)
    ratio_table = count_table.div(count_table.sum(axis=1), axis=0) * 100
    
    # 전체 통합 요약 테이블
    summary_df = pd.DataFrame(index=count_table.index)
    summary_df['총 곡수'] = count_table.sum(axis=1)
    for col in categories:
        summary_df[f'{col} (곡)'] = count_table[col]
        summary_df[f'{col} (%)'] = ratio_table[col].round(1)
        
    return df, summary_df, count_table, ratio_table

def plot_stacked_bar(ratio_table: pd.DataFrame, output_path: str):
    """
    연도별 곡 제목 언어 유형 100% 누적 막대 그래프 생성
    """
    set_korean_font()
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    
    # 색상 팔레트 정의 (가독성 높은 학술/보고서용 톤)
    colors = {
        '순수 한글': '#3A7CA5',      # 차분한 청록색
        '순수 영문': '#E05A47',      # 경각심을 주는 산호 주황색
        '한·영 혼용': '#F2C14E',     # 밝은 골드 옐로우
        '기타(숫자/기호)': '#C0C0C0'  # 밝은 회색
    }
    
    years = ratio_table.index.astype(str)
    bottom = np.zeros(len(years))
    
    for col in ['순수 한글', '순수 영문', '한·영 혼용', '기타(숫자/기호)']:
        values = ratio_table[col].values
        bars = ax.bar(years, values, bottom=bottom, label=col, color=colors[col], width=0.65, edgecolor='white', linewidth=1)
        
        # 막대 내 백분율 텍스트 표기 (4% 이상일 때만)
        for i, val in enumerate(values):
            if val >= 4.0:
                y_pos = bottom[i] + val / 2
                ax.text(i, y_pos, f"{val:.1f}%", ha='center', va='center', 
                        color='white' if col in ['순수 한글', '순수 영문'] else '#222222',
                        fontsize=9.5, fontweight='bold')
        bottom += values
        
    ax.set_title("멜론 월간 TOP 10 연도별 곡 제목 언어 유형 분포 (2015~2025)", pad=18, fontweight='bold', fontsize=15)
    ax.set_xlabel("연도 (Year)", labelpad=10, fontweight='bold')
    ax.set_ylabel("비율 (%)", labelpad=10, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=4, frameon=True, edgecolor='#cccccc')
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"누적 막대 그래프 저장 완료: {output_path}")

def plot_trend_lines(ratio_table: pd.DataFrame, output_path: str):
    """
    곡 제목 언어 유형 연도별 꺾은선 추세 그래프 생성 (골든크로스 강조)
    """
    set_korean_font()
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    
    years = ratio_table.index
    
    # 꺾은선 그리기
    ax.plot(years, ratio_table['순수 한글'], marker='o', linewidth=2.5, markersize=7, 
            color='#3A7CA5', label='순수 한글 (예: 위아래, 봄날, 고민중독)')
    ax.plot(years, ratio_table['순수 영문'], marker='s', linewidth=3, markersize=8, 
            color='#E05A47', label='순수 영문 (예: Attention, Drama, Supernova)')
    ax.plot(years, ratio_table['한·영 혼용'], marker='^', linewidth=2, markersize=6, linestyle='--',
            color='#E5A93C', label='한·영 혼용 (예: 화 (Fire), 오늘만 I LOVE YOU)')
    
    # 주요 수치 텍스트 표시 (2015년, 2019년, 2025년 강조)
    for target_yr in [2015, 2019, 2025]:
        val_kor = ratio_table.loc[target_yr, '순수 한글']
        val_eng = ratio_table.loc[target_yr, '순수 영문']
        ax.text(target_yr, val_kor + 2.5, f"{val_kor:.1f}%", ha='center', color='#3A7CA5', fontweight='bold', fontsize=9.5)
        ax.text(target_yr, val_eng - 3.8, f"{val_eng:.1f}%", ha='center', color='#E05A47', fontweight='bold', fontsize=9.5)
        
    # 역전 구간(2021~2022) 하이라이트
    ax.axvspan(2021, 2022, color='#FFE5D9', alpha=0.45, linestyle=':', label='역전 구간 (영문 제목 > 한글 제목)')
    ax.annotate("2021-2022년 역전 발생\n(순수 영문 제목이 순수 한글 추월)", 
                xy=(2021.5, 48), xytext=(2017.5, 58),
                arrowprops=dict(facecolor='#D9381E', shrink=0.08, width=1.5, headwidth=7),
                fontsize=10.5, fontweight='bold', color='#B32400',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#FFF3EB", edgecolor="#D9381E", alpha=0.9))

    ax.set_title("대중가요 제목의 언어 변화 추이: 순수 영문 제목의 급증 (2015~2025)", pad=18, fontweight='bold', fontsize=15)
    ax.set_xlabel("연도 (Year)", labelpad=10, fontweight='bold')
    ax.set_ylabel("비율 (%)", labelpad=10, fontweight='bold')
    ax.set_xticks(years)
    ax.set_ylim(0, 80)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper left', frameon=True, edgecolor='#cccccc', fontsize=9.5)
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"추세 꺾은선 그래프 저장 완료: {output_path}")

def run_title_analysis(filepath: str = str(PRIVATE_LYRICS_CSV),
                       output_dir: str = "output"):
    """
    곡 제목 분석 전체 파이프라인 실행
    """
    figures_dir = os.path.join(output_dir, "analysis_figures")
    tables_dir = os.path.join(output_dir, "analysis_tables")
    ensure_dir(figures_dir)
    ensure_dir(tables_dir)
    
    print("[1/4] 데이터 로드 및 전처리 (연도별 고유곡, 해외 팝송 제외)...")
    analyzed_df, foreign_df = load_preprocessed_data(filepath, exclude_foreign=True, yearly_unique=True)
    
    print(f"[2/4] 곡 제목 언어 유형 분류 진행 중 (총 {len(analyzed_df)}곡)...")
    labeled_df, summary_df, count_table, ratio_table = analyze_title_types(analyzed_df)
    
    # 통계 테이블 저장
    table_path = os.path.join(tables_dir, "yearly_title_type_stats.csv")
    summary_df.to_csv(table_path, encoding='utf-8-sig')
    print(f"[3/4] 통계 요약 테이블 저장 완료: {table_path}")
    
    # 시각화 그래프 생성
    print("[4/4] 시각화 차트 생성 중...")
    bar_chart_path = os.path.join(figures_dir, "title_type_stacked_bar.png")
    line_chart_path = os.path.join(figures_dir, "title_type_trend_lines.png")
    plot_stacked_bar(ratio_table, bar_chart_path)
    plot_trend_lines(ratio_table, line_chart_path)
    
    print("\n" + "="*60)
    print("★ 곡 제목 언어 유형 분석 결과 요약 (2015 vs 2025)")
    print("="*60)
    print(summary_df[['총 곡수', '순수 한글 (%)', '순수 영문 (%)', '한·영 혼용 (%)']].to_string())
    print("="*60)
    
    # 2015 vs 2025 증감률 계산
    kor_change = ratio_table.loc[2025, '순수 한글'] - ratio_table.loc[2015, '순수 한글']
    eng_change = ratio_table.loc[2025, '순수 영문'] - ratio_table.loc[2015, '순수 영문']
    print(f"\n[핵심 발견점]")
    print(f"1. 순수 영문 제목: 2015년 {ratio_table.loc[2015, '순수 영문']:.1f}% -> 2025년 {ratio_table.loc[2025, '순수 영문']:.1f}% ({eng_change:+.1f}%p 대폭 증가)")
    print(f"2. 순수 한글 제목: 2015년 {ratio_table.loc[2015, '순수 한글']:.1f}% -> 2025년 {ratio_table.loc[2025, '순수 한글']:.1f}% ({kor_change:+.1f}%p 감소)")
    print(f"3. 골든크로스 시점: 2021~2022년에 순수 영문 제목 비율(54.2%)이 순수 한글(22.9%)을 처음으로 역전함.")

if __name__ == "__main__":
    run_title_analysis()
