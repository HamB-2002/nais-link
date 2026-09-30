# 활용 내역 (생성형 AI · 오픈소스 · 외부 데이터)

누락하거나 허위로 적으면 실격이다. 쓰는 즉시 한 줄 추가한다.

## 생성형 AI

### 개발에 쓴 AI 도구 (사람별)
Codex, Claude Code, ChatGPT, Copilot, Gemini 등 **쓰는 도구는 전부**, 본인 표에 적는다.

- 표는 **용도별로 한 줄**이다. 같은 용도에 쓰는 도구나 모델이 바뀌어도 **같은 칸 안에 함께** 적는다(예: `Codex · 모델명, Claude Code · 모델명`). 새로운 용도가 생기면 새 줄을 추가한다.
- 기존에 적은 것은 지우지 않고 덧붙인다.
- 모델명·버전은 도구 화면에서 확인한 이름 그대로 적는다(예: Claude Code 하단 상태줄이나 `/model`, Codex의 `/model`). 모르면 「확인 필요」로 적고 나중에 채운다.
- 각자 **자기 표만** 고치면 서로 충돌하지 않는다.

#### 정재화 (@HamB-2002)
| 용도 | 도구 · 모델·버전 |
|---|---|
| 저장소 구성, 시험 자료 탐색·변환·문서화 | Claude Code (데스크톱 앱) · Claude Sonnet 5.5 (`claude-sonnet-5-5`) |

#### 김종욱 (@kim0701-bit)
| 용도 | 도구 · 모델·버전 |
|---|---|
| 보고서 표·코드 재실행 결과 대조 기준, 표 정규화·의미 검증·5단계 판정 프롬프트 설계 | Codex (터미널) · ChatGPT Pro |

#### 석정연 (@suk-jy)
| 용도 | 도구 · 모델·버전 |
|---|---|
| 보고서 수치 추출·표 셀 처리 로직 설계 및 피드백, 검증 대상 수치 분류 기준 설계·수정, 수치 결과표 구현, HWPX 통합 테스트·성능 분석 | ChatGPT (GPT-5.6 Sol) · Codex (터미널) |

#### 이형호 (@ihertn00)
| 용도 | 도구 · 모델·버전 |
|---|---|
| 숫자내력 프롬프트 설계·수정, 보고서 수치 추출·원본 데이터 및 분석 코드 재실행 대조, Python·R 실행 환경 구성, JSON 결과·Streamlit 검토 화면 구현, Git 저장소 문서화 | Codex 0.159.2 · gpt-5.6-luna |

#### 신혜원 (@a99812100-blip)
| 용도 | 도구 · 모델·버전 |
|---|---|
| (작성 예정) |  |

### 제품 안에서 호출하는 AI 모델
우리 도구가 실행 중에 부르는 모델이다. API 모델과 로컬 모델을 모두 적는다.

| 용도 | 모델·버전 | 실행 방식 (API / 로컬) | 담당 파트 |
|---|---|---|---|
| 수치 검증 대상 판별 · 코드 후보 선택 · 차이 원인 분류 | (본선에서 확정) | | 코드·실행 / 문서·수치 |

## 오픈소스
| 이름 | 라이선스 | 용도 | 파트 |
|---|---|---|---|
| pypandoc-hwpx 0.1.1 | MIT | docx·md·LaTeX→hwpx 변환 (`sample-10-hwpx`, `sample-12-hwpx`, `sample-13-hwpx` 생성) | 시험 자료 준비 |
| Pillow 12.3.0 | MIT-CMU | 위 변환 도구가 그림 크기를 계산하는 데 쓰는 의존 패키지 (저장소에 포함하지 않음) | 시험 자료 준비 |
| pypandoc 1.17 (pypandoc_binary) / Pandoc 3.9 | MIT / GPL-2.0-or-later | 위 변환의 실행 엔진 (실행 도구로만 사용) | 시험 자료 준비 |
| python-hwpx 6.6.0 | Apache-2.0 | 변환본이 hwpx로 열리는지 구조 확인 | 시험 자료 준비 |
| python-docx / lxml | MIT / BSD-3-Clause | 변환 전후 표·글자·숫자 비교 검증, docx 그림 제거(`sample-11-modified`) | 시험 자료 준비 |
| pandas 3.0.6 · numpy 2.5.3 · scipy 1.18.1 | BSD-3-Clause | 시험 자료(`sample-12`, `sample-13`) 코드 재실행 확인 (저장소에 포함하지 않음) | 시험 자료 준비 |
| matplotlib 3.11.2 | Matplotlib License (PSF 기반) | 위와 같음 (그림 생성) | 시험 자료 준비 |
| kiwipiepy 0.24.0 | Apache-2.0 (PyPI 표기) | `sample-12` 코드 재실행 확인 (저장소에 포함하지 않음) | 시험 자료 준비 |
| pypdf 6.19.0 · openpyxl 3.1.5 | BSD-3-Clause · MIT | 시험 자료의 PDF 본문·엑셀 확인 (저장소에 포함하지 않음) | 시험 자료 준비 |

## 외부 데이터
| 이름 | 출처 URL | 라이선스 | 용도 |
|---|---|---|---|
| 행정안전부_공공데이터 활용기업 실태조사 결과 (2016~2025 HWPX) | https://www.data.go.kr/data/15038611/fileData.do | 공공저작물 : 출처표시 (제 1유형) | HWPX 수치·표·그래프 추출 및 원자료 대조 테스트 |
| 한국지능정보사회진흥원_공공데이터 활용기업 실태조사 raw data (2016~2025) | https://www.data.go.kr/data/15120672/fileData.do | 이용허락범위 제한 없음 | 보고서 수치의 원자료 대조 테스트 |
| Demand for “Safe Spaces”: Avoiding Harassment and Stigma 재현 패키지 | https://github.com/worldbank/rio-safe-space | CC0 1.0 Universal (`Reproducibility Package/LICENSE`) | PDF 수치 추출·Stata/R 코드 위치 탐색·비식별 원자료 재실행 테스트 |
| Learning Poverty Working Paper 재현 패키지 | https://github.com/worldbank/LearningPoverty/tree/v1.1/05_working_paper | MIT License | PDF 수치 추출·Stata 코드 위치 탐색·CSV/XLSX 입력 재실행 테스트 |
| 「미술현장의 정보격차 해소를 위한 생성형 AI 기반 '광역 리서치' 실행연구」 보충자료 (Kim, Kyu hyung, Chonnam National University) | https://zenodo.org/records/22157092 (DOI 10.5281/zenodo.22157092) | CC BY 4.0 | 한국어 docx 보고서의 수치 추출, 코드·데이터 대조 테스트, hwpx 변환 시험 (`sample-10`, `sample-10-hwpx`) |
| 「환경아카이브 풀숲 · 환경사진아카이브 · 공간풀숲 임팩트 측정 보고서」 v1.1 (재단법인 숲과나눔) | https://github.com/ArchivelabEdu/ecoarchive-impact2026 (커밋 61265f8) | MIT License | 한국어 docx 보고서 수치의 정제 CSV·원자료 대조 시험 (`sample-11-modified`, 그림 제거·일부 파일 제외) |
| 「대중가요 제목·가사 표기 분석 (2015–2025)」 (mksdr) | https://github.com/mksdr/kpop-title-lyrics-analysis (커밋 bdf2b16) | GPL-3.0 | 한국어 md 보고서 수치의 코드 재실행 대조, 원본 650행과 공개 260행의 차이로 값이 어긋나는 사례 (`sample-12`) |
| *Outcome Without Method: An Outcome-Validation Integrity Score for Agentic Cybersecurity Benchmarks* (Babar Khan Akhunzada, SecurityWall) | https://zenodo.org/records/22016351 (DOI 10.5281/zenodo.22016351) | CC BY 4.0 | 영어 PDF 보고서 수치의 파이썬 코드 재실행 대조 (`sample-13`) |
