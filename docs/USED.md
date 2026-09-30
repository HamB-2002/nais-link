# 활용 내역 (생성형 AI · 오픈소스 · 외부 데이터)

누락하거나 허위로 적으면 실격이다. 쓰는 즉시 한 줄 추가한다.

## 생성형 AI
| 용도 | 모델·버전 | 쓰는 파트 |
|---|---|---|
| 코드 작성 보조 | Codex (모델·버전 확정 후 기재) | 전원 |
| 코드 작성 보조 | Claude Code | 전원 |
| 수치 검증 대상 판별 · 코드 후보 선택 · 차이 원인 분류 | (본선에서 확정) | 코드·실행 / 문서·수치 |

## 오픈소스
| 이름 | 라이선스 | 용도 | 파트 |
|---|---|---|---|
| pypandoc-hwpx 0.1.1 | MIT | docx→hwpx 변환 (`sample-10-hwpx` 생성) | 시험 자료 준비 |
| pypandoc 1.17 (pypandoc_binary) / Pandoc 3.9 | MIT / GPL-2.0-or-later | 위 변환의 실행 엔진 (실행 도구로만 사용) | 시험 자료 준비 |
| python-hwpx 6.6.0 | Apache-2.0 | 변환본이 hwpx로 열리는지 구조 확인 | 시험 자료 준비 |
| python-docx / lxml | MIT / BSD-3-Clause | 변환 전후 표·글자·숫자 비교 검증 | 시험 자료 준비 |

## 외부 데이터
| 이름 | 출처 URL | 라이선스 | 용도 |
|---|---|---|---|
| 행정안전부_공공데이터 활용기업 실태조사 결과 (2016~2025 HWPX) | https://www.data.go.kr/data/15038611/fileData.do | 공공저작물 : 출처표시 (제 1유형) | HWPX 수치·표·그래프 추출 및 원자료 대조 테스트 |
| 한국지능정보사회진흥원_공공데이터 활용기업 실태조사 raw data (2016~2025) | https://www.data.go.kr/data/15120672/fileData.do | 이용허락범위 제한 없음 | 보고서 수치의 원자료 대조 테스트 |
| Demand for “Safe Spaces”: Avoiding Harassment and Stigma 재현 패키지 | https://github.com/worldbank/rio-safe-space | CC0 1.0 Universal (`Reproducibility Package/LICENSE`) | PDF 수치 추출·Stata/R 코드 위치 탐색·비식별 원자료 재실행 테스트 |
| Learning Poverty Working Paper 재현 패키지 | https://github.com/worldbank/LearningPoverty/tree/v1.1/05_working_paper | MIT License | PDF 수치 추출·Stata 코드 위치 탐색·CSV/XLSX 입력 재실행 테스트 |
| 「미술현장의 정보격차 해소를 위한 생성형 AI 기반 '광역 리서치' 실행연구」 보충자료 (Kim, Kyu hyung, Chonnam National University) | https://zenodo.org/records/22157092 (DOI 10.5281/zenodo.22157092) | CC BY 4.0 | 한국어 docx 보고서의 수치 추출, 코드·데이터 대조 테스트, hwpx 변환 시험 (`sample-10`, `sample-10-hwpx`) |
