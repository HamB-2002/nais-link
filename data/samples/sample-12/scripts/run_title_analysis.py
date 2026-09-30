"""
곡 제목 분석 실행 스크립트
실행 방법: python run_title_analysis.py
"""

import sys
import os

# 현재 경로를 sys.path에 추가하여 src 모듈 임포트 지원
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from title_analysis import run_title_analysis

if __name__ == "__main__":
    run_title_analysis()
