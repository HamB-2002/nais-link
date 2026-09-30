"""
대중가요 가사 분석 실행 스크립트
실행 방법: python run_lyrics_analysis.py
"""

import sys
import os

# 현재 경로를 sys.path에 추가하여 src 모듈 임포트 지원
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lyrics_analysis import get_or_create_processed_lyrics, run_lyrics_statistical_analysis

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
            
    print("=== [멜론 차트 가사 데이터 전처리 및 통계 분석] ===")
    df = get_or_create_processed_lyrics(force_recompute=False)
    print(f"로드 완료: 총 {len(df)}곡, {len(df.columns)}개 특성 컬럼\n")
    results = run_lyrics_statistical_analysis(df)
