# Stock Advisor

미국 주식 투자 진입 타이밍을 AI 스코어링으로 분석하는 프로그램입니다. 20개 이상의 기술적/퀀트/매크로 지표를 종합하여 0~100점 스코어와 A~F 등급을 산출하고, Streamlit 대시보드로 시각화합니다.

## 주요 기능

- **종목 분석**: 티커 입력 시 매크로 환경, 기술적 분석, 패턴 분석, 퀀트 팩터를 종합한 AI 스코어 산출
- **인덱스 스크리닝**: NASDAQ 100 / S&P 500 / Russell 2000 전 종목을 분석하여 Top N 추천
- **웹 대시보드**: Streamlit 기반의 인터랙티브 차트 및 지표 카드 UI
- **CLI 지원**: 터미널에서 빠르게 분석 및 스크리닝 실행

## 프로젝트 구조

```
stock-advisor/
├── main.py                  # 엔트리포인트 (CLI + 분석 파이프라인)
├── requirements.txt         # 의존성 목록
├── .env.example             # 환경변수 템플릿
│
├── config/                  # 설정
│   ├── settings.py          # API 키, 캐시 TTL, 분석 기본값
│   └── scoring_weights.py   # 스코어링 가중치 및 등급 기준
│
├── data/                    # 데이터 수집 레이어
│   ├── fetcher.py           # 데이터 수집 오케스트레이터
│   ├── yahoo_client.py      # yfinance 래퍼 (가격, 정보, 옵션, 기관 보유)
│   ├── fred_client.py       # FRED API 래퍼 (금리, 수익률 곡선)
│   ├── finviz_client.py     # Finviz 래퍼 (공매도, 펀더멘탈)
│   ├── cache_manager.py     # diskcache 기반 캐싱
│   └── index_constituents.py # 인덱스 구성 종목 조회
│
├── analysis/                # 분석 엔진
│   ├── macro/               # 매크로 분석
│   │   ├── macro_analyzer.py    # 금리, VIX, 유가, 금, S&P500 종합 분석
│   │   └── market_breadth.py    # 시장 브레드스 (placeholder)
│   │
│   ├── technical/           # 기술적 분석
│   │   ├── trend_analyzer.py     # SMA 정배열/역배열, ADX 추세 강도
│   │   ├── momentum_analyzer.py  # RSI, MACD, 스토캐스틱, 골든/데드 크로스
│   │   ├── volume_analyzer.py    # OBV, VWAP, 볼륨 프로파일 (POC/VAH/VAL)
│   │   ├── ichimoku_analyzer.py  # 일목균형표 전체 분석
│   │   └── fibonacci_analyzer.py # 피보나치 되돌림 레벨
│   │
│   ├── pattern/             # 패턴 분석
│   │   ├── wave_analyzer.py       # 엘리엇 파동 (ZigZag 기반)
│   │   ├── fvg_analyzer.py        # Fair Value Gap (가격 불균형 영역)
│   │   ├── candlestick_pattern.py # 캔들스틱 패턴 인식 (6종)
│   │   ├── similarity_analyzer.py # 과거 패턴 유사도 매칭 (코사인 유사도)
│   │   └── complex_pattern.py     # 복합 패턴 감지 (7가지 시나리오)
│   │
│   └── quant/               # 퀀트 팩터
│       ├── short_squeeze.py      # 공매도 스퀴즈 포텐셜
│       ├── rsi_divergence.py     # RSI 다이버전스 (정규/히든)
│       ├── bb_squeeze.py         # 볼린저 밴드 스퀴즈 (켈트너 채널 비교)
│       ├── mean_reversion.py     # 평균 회귀 Z-Score
│       ├── momentum_factor.py    # 12-1 모멘텀 팩터
│       ├── sector_relative.py    # 섹터 상대강도 순위
│       ├── earnings_surprise.py  # 어닝 서프라이즈 및 연속 비트
│       ├── institutional_flow.py # 기관 투자자 수급 분석
│       ├── options_flow.py       # 옵션 풋/콜 비율, IV Rank
│       └── lunar_phase.py        # 달 위상 (실험적 지표)
│
├── scoring/                 # 스코어링 엔진
│   ├── score_engine.py      # 가중 합산 총점 계산
│   ├── grade_system.py      # A~F 등급 매핑
│   ├── target_calculator.py # 목표가/손절가 산출
│   ├── signal_compositor.py # 최종 매매 신호 문자열 생성
│   ├── alert_generator.py   # 주요 알림 생성
│   └── screener.py          # 인덱스 배치 스크리닝
│
├── ui/                      # Streamlit 대시보드
│   ├── streamlit_app.py     # 메인 앱 (종목 분석 + 스크리너 탭)
│   └── components/          # UI 컴포넌트
│       ├── macro_bar.py         # 매크로 상태 배지
│       ├── score_card.py        # AI 점수 + 등급 카드
│       ├── price_chart.py       # 캔들스틱 차트 (Plotly)
│       ├── indicator_cards.py   # 20개 지표 카드 그리드
│       ├── target_panel.py      # 목표가/손절가 패널
│       ├── alert_panel.py       # 알림 패널
│       └── screener_panel.py    # 스크리너 결과 테이블
│
├── models/
│   └── schemas.py           # Pydantic 데이터 모델 (전체 분석 결과 스키마)
│
└── utils/                   # 유틸리티
    ├── helpers.py           # 정규화, 안전 나눗셈, 스윙 하이/로우 탐지
    ├── formatters.py        # 숫자 포맷팅 (가격, 퍼센트, 대형 숫자)
    └── ta_utils.py          # 순수 pandas/numpy 기술적 지표 라이브러리
```

## 스코어링 체계

총점은 6개 카테고리의 가중 합산으로 산출됩니다:

| 카테고리 | 비중 | 구성 요소 |
|---------|------|----------|
| 매크로 환경 | 10% | 금리, VIX, 유가/금, 시장 브레드스 |
| 추세/모멘텀 | 25% | 추세 방향/강도, RSI/MACD, 일목균형표 |
| 거래량/수급 | 20% | OBV, 볼륨 프로파일, 기관 수급, 옵션 플로우 |
| 패턴/구조 | 20% | 파동, FVG, 피보나치, 유사도, 캔들스틱 |
| 퀀트 팩터 | 15% | 평균 회귀, 모멘텀, 섹터 상대강도, 어닝 |
| 리스크/특수 | 10% | 공매도 스퀴즈, 특수 신호, 복합 패턴 |

### 등급 기준

| 등급 | 점수 범위 | 의미 |
|-----|----------|------|
| A | 80 ~ 100 | 강력 매수 구간 |
| B | 65 ~ 79 | 매수 고려 |
| C | 45 ~ 64 | 중립 / 관망 |
| D | 25 ~ 44 | 매도 고려 |
| F | 0 ~ 24 | 강력 매도 구간 |

## 설치 및 실행

### 1. 의존성 설치

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
# .env 파일에 FRED_API_KEY 설정 (선택사항 - 없어도 기본 동작)
```

### 3. 실행

**종목 분석 (CLI)**
```bash
python main.py AAPL
```

**인덱스 스크리닝 (CLI)**
```bash
python main.py screen                    # 전체 인덱스 스크리닝
python main.py screen "NASDAQ 100"       # NASDAQ 100만 스크리닝
python main.py screen "S&P 500" 10       # S&P 500 Top 10
```

**웹 대시보드**
```bash
streamlit run ui/streamlit_app.py
```

## 데이터 소스

| 소스 | 용도 | API 키 |
|-----|------|--------|
| [yfinance](https://github.com/ranaroussi/yfinance) | 가격, 재무, 옵션, 기관 보유 | 불필요 |
| [FRED API](https://fred.stlouisfed.org/) | 금리, 수익률 곡선 | 선택 (`.env`) |
| [Finviz](https://finviz.com/) | 공매도, 펀더멘탈, 인덱스 구성 종목 | 불필요 |

## 기술 스택

- **Python 3.12+**
- **pandas / numpy / scipy / scikit-learn** - 데이터 처리 및 분석
- **Plotly** - 인터랙티브 차트
- **Streamlit** - 웹 대시보드
- **Pydantic** - 데이터 모델 검증
- **diskcache** - 디스크 기반 캐싱
- **ephem** - 달 위상 계산

## 면책 조항

이 프로그램은 교육 및 연구 목적으로 제작되었습니다. 투자 권유가 아니며, 실제 투자 결정에 대한 책임은 사용자에게 있습니다.
