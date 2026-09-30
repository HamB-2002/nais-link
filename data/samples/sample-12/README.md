# 대중가요 제목·가사 표기 분석 (2015–2025)

멜론 월간 TOP 10 표본의 등록 제목과 가사에 나타나는 한글·영문 문자 구성을 기술통계로 정리한 연구 자료입니다. 분석 단위는 한 곡을 한 해에 한 번 세는 **곡-연도 관측치**입니다.

## 확인 가능한 핵심 수치

- 원 분석은 650개 곡-연도 관측치(고유 제목·가수 조합 584개)를 사용했습니다. 공개 곡별 데이터는 저작권을 고려해 이 중 2/5인 260행만 제공합니다.
- 등록 제목에서 영문 알파벳은 있고 한글은 없는 유형은 2015년 20/89건(22.5%), 2025년 21/36건(58.3%)입니다.
- 곡별 영문 문자 비율의 연도별 산술평균은 2015년 26.53%, 2025년 54.14%입니다. 이 비율은 영문 알파벳 수를 한글 음절 글자 수와 영문 알파벳 수의 합으로 나눈 값입니다.

이 값들은 원 분석 650행의 표본 내 기술통계입니다. 공개 CSV는 일부만 담고 있으므로 그 파일에서 다시 계산한 값과 다를 수 있습니다. 전체 음원·실제 청취량·변화 원인을 나타내지 않습니다. 정의와 검증 범위는 [METHODS.md](METHODS.md), 연도별 결과는 [RESULTS.md](RESULTS.md)에 정리했습니다.

## 자료와 결과물

| 위치 | 내용 |
| --- | --- |
| `datasets/lyrics_metrics.csv` | 가사 원문 및 추출 어휘 문자열을 제외한 곡-연도별 수치·분류 자료 (원 분석 650행 중 공개 260행) |
| `datasets/yearly_title_type_stats.csv` | 연도별 등록 제목 유형 집계 |
| `datasets/title_credit_sensitivity.csv` | 참여자 표기 제거로 제목 문자열이 바뀐 106건의 전후 대조 |
| `datasets/title_credit_yearly_comparison.csv` | 참여자 표기 제거 전후의 연도별 제목 유형 집계 |
| `output/analysis_tables/lyrics_yearly_summary.csv` | 연도별 가사 지표 집계 |
| `output/analysis_tables/title_lyrics_cross_analysis.csv` | 등록 제목 유형별 가사 지표 집계 |
| `figures/` | 보고서 및 문서에서 참조하는 결과 그림 |
| `scripts/` | 분석, 시각화 및 수집 코드 |

> **저작권 및 데이터 보호 안내**: 저작권을 고려해 곡별 지표는 원 분석 자료의 2/5만 공개합니다. 가사 원문, 원문이 포함된 전처리 파일, 곡별 가사에서 추출한 형태소 목록은 공개 자료에 포함하지 않습니다. 수집기 실행 시 생성되는 `private_data/` 디렉터리는 `.gitignore`에 등록되어 원자료가 공개 저장소에 커밋되지 않도록 보호됩니다.

## 빠른 시작 및 분석 재현

공개된 곡별 지표(`datasets/lyrics_metrics.csv`)로 공개본 260행에 대한 통계표와 시각화를 생성할 수 있습니다. 저장소의 기존 집계표·그림은 원 분석 650행을 기준으로 하므로 재실행 결과와 다를 수 있습니다. 상위 어휘 그림은 공개본에 없는 곡별 형태소 자료를 사용했습니다.

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate

# 의존성 패키지 설치
python -m pip install -r requirements.txt
```

### 2. 분석 및 시각화 실행

```bash
# 1) 곡 제목 언어 유형 분석 및 누적 막대·추세선 차트 생성
python scripts/run_title_analysis.py

# 2) 가사 지표(영문 비율, TTR, 대명사 등) 통계 요약 및 시각화 재생성
python scripts/run_lyrics_analysis.py
```

- 실행 결과는 `output/analysis_tables/`, `output/analysis_figures/`, `figures/`에 각각 저장됩니다.

## 수집기 안내 (선택 사항)

음원 차트 및 가사 원문을 새로 수집하는 스크립트는 로컬 전용으로 제공됩니다:

```powershell
python scripts/downloader/main.py
python scripts/downloader/bugs_lyrics_fetcher.py
```

첫 번째 스크립트는 차트 메타데이터를 `private_data/collected/raw_chart_metadata.csv`에 저장하고, 두 번째 스크립트는 해당 파일을 입력으로 받아 가사 포함 자료를 같은 로컬 전용 폴더에 저장합니다. 외부 서비스에 접속하므로 재수집 결과가 기존 분석 입력과 같다고 보장할 수 없습니다.

자세한 분석 방법론과 한계는 [METHODS.md](METHODS.md)를 참고하세요.

## 라이선스

`LICENSE`의 GPL-3.0은 저장소의 소프트웨어 코드에 적용됩니다. 이 라이선스가 제3자 자료나 데이터의 이용 권한을 부여하지는 않습니다.
