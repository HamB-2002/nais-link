"""공통 그래프 스타일 및 출력 디렉터리 유틸리티."""

import os
import matplotlib.pyplot as plt

import logging
import platform

# matplotlib 글꼴 탐색 경고 억제
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

def set_korean_font():
    """운영체제에 설치된 최적의 한글 글꼴을 감지하여 사용합니다."""
    system = platform.system()
    if system == 'Windows':
        fonts = ['Malgun Gothic', '맑은 고딕', 'sans-serif']
    elif system == 'Darwin':
        fonts = ['AppleGothic', 'sans-serif']
    else:
        fonts = ['NanumGothic', 'Noto Sans CJK KR', 'DejaVu Sans', 'sans-serif']

    plt.rcParams['font.family'] = fonts
    plt.rcParams['axes.unicode_minus'] = False
    
    # 그래프 기본 스타일 설정
    plt.rcParams['figure.autolayout'] = True
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10

def ensure_dir(path: str):
    """디렉토리가 없으면 생성"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
