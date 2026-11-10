import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random
import time
from datetime import datetime
from matplotlib.colors import ListedColormap


# =========================================================
# 1. 기본 설정
# =========================================================

st.set_page_config(
    page_title="EUV 반도체 타이쿤",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 2. 전체 사이트 디자인 및 글씨 가독성
# =========================================================

st.markdown("""
<style>

/* 전체 배경 */
.stApp {
    background: linear-gradient(
        135deg,
        #08111f 0%,
        #101d32 55%,
        #0b1424 100%
    ) !important;

    color: #f8fafc !important;
}

/* 모든 기본 글씨 */
.stApp p,
.stApp li,
.stApp label,
.stApp span,
.stApp strong,
.stApp small,
.stApp div {
    color: #e2e8f0;
}

/* 제목 */
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp h5,
.stApp h6 {
    color: #ffffff !important;
    font-weight: 750 !important;
}

/* 본문 */
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: #e2e8f0 !important;
}

/* 설명 글씨 */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
    color: #b5c4d8 !important;
}

/* 상단 헤더 */
[data-testid="stHeader"] {
    background: transparent !important;
}

/* 사이드바 */
[data-testid="stSidebar"] {
    background: #101b2c !important;
    border-right: 1px solid #334155;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #f1f5f9 !important;
}

/* 통계 카드 */
[data-testid="stMetric"] {
    background: #172940 !important;
    border: 1px solid #344b69 !important;
    border-radius: 15px !important;
    padding: 16px !important;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p {
    color: #cbd5e1 !important;
}

[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div {
    color: #ffffff !important;
    font-weight: 800 !important;
}

[data-testid="stMetricDelta"] {
    color: #6ee7b7 !important;
}

/* 버튼 */
.stButton button,
.stDownloadButton button {
    color: #ffffff !important;
    background: #1e4975 !important;
    border: 1px solid #4b83b6 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
}

.stButton button:hover,
.stDownloadButton button:hover {
    background: #2563a5 !important;
    border-color: #38bdf8 !important;
    color: #ffffff !important;
}

/* 버튼 내부 글씨 */
.stButton button p,
.stButton button span {
    color: #ffffff !important;
}

/* 비활성 버튼 */
.stButton button:disabled {
    color: #aebed2 !important;
    background: #26364c !important;
    border-color: #475569 !important;
}

/* 입력창 */
.stApp input,
.stApp textarea {
    background: #172940 !important;
    color: #ffffff !important;
    border: 1px solid #48617f !important;
    caret-color: #38bdf8 !important;
}

/* 입력창 안내 글씨 */
.stApp input::placeholder,
.stApp textarea::placeholder {
    color: #b5c4d8 !important;
}

/* 선택 메뉴 */
[data-baseweb="select"] > div {
    background: #172940 !important;
    border-color: #48617f !important;
}

[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color: #ffffff !important;
}

/* 선택 메뉴 팝업 */
[data-baseweb="popover"],
[data-baseweb="menu"],
[role="listbox"],
[role="option"] {
    background: #172940 !important;
    color: #ffffff !important;
}

[role="option"]:hover {
    background: #285078 !important;
}

/* 슬라이더 설명 */
[data-testid="stWidgetLabel"] p {
    color: #ffffff !important;
    font-weight: 650 !important;
}

/* 탭 */
[data-testid="stTabs"] button {
    color: #dbeafe !important;
    font-weight: 700 !important;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: #38bdf8 !important;
}

/* 표 */
[data-testid="stDataFrame"] {
    border: 1px solid #344b69 !important;
    border-radius: 12px !important;
    overflow: hidden;
}

/* 알림창 */
[data-testid="stAlert"] p,
[data-testid="stAlert"] div {
    color: #ffffff !important;
}

/* 구분선 */
hr {
    border-color: #334155 !important;
}

/* 카드 디자인 */
.card {
    background: #14243a;
    border: 1px solid #344b69;
    border-radius: 15px;
    padding: 18px;
    margin-bottom: 12px;
}

/* 상단 메인 배너 */
.hero {
    background: linear-gradient(
        110deg,
        #153456,
        #14243a,
        #102039
    );
    border: 1px solid #38638a;
    border-radius: 20px;
    padding: 25px;
    margin-bottom: 20px;
}

.hero-title {
    color: #ffffff !important;
    font-size: 30px;
    font-weight: 850;
}

.hero-sub {
    color: #d4e2f2 !important;
    font-size: 15px;
}

.hero-label {
    color: #7dd3fc !important;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 3px;
}

/* 섹션 라벨 */
.section-label {
    color: #7dd3fc !important;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
}

/* 상태 표시 */
.status-live {
    color: #6ee7b7 !important;
    background: #123d32;
    border: 1px solid #2e8b6b;
    border-radius: 20px;
    padding: 7px 13px;
    font-weight: 800;
}

.status-stop {
    color: #e2e8f0 !important;
    background: #334155;
    border: 1px solid #64748b;
    border-radius: 20px;
    padding: 7px 13px;
    font-weight: 800;
}

/* 강조 숫자 */
.big-number {
    color: #ffffff !important;
    font-size: 28px;
    font-weight: 850;
}

/* 게임 기록 */
.log-item {
    color: #e2e8f0 !important;
    background: #14243a;
    border-left: 3px solid #38bdf8;
    border-radius: 5px;
    padding: 10px;
    margin-bottom: 7px;
    font-size: 13px;
}

/* 안내 문구 */
.small-note {
    color: #cbd5e1 !important;
    font-size: 13px;
}

/* 페이지 여백 */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 3. 게임 설정
# =========================================================

BATCH_INTERVAL = 4.0
FRAME_SLEEP = 0.25

STAGES = {
    1: {
        "name": "기본 EUV 공정",
        "freq_range": (30, 100),
        "reward": 300,
        "unlock_at": 0
    },

    2: {
        "name": "고정밀 EUV 공정",
        "freq_range": (25, 110),
        "reward": 420,
        "unlock_at": 15
    },

    3: {
        "name": "차세대 EUV 공정",
        "freq_range": (20, 120),
        "reward": 600,
        "unlock_at": 40
    }
}

CONTRACTS = {
    "high_quality": {
        "title": "고수율 납품 계약",
        "description": "수율 90% 초과 웨이퍼 5장 생산",
        "target": 5,
        "reward": 1800,
        "condition": "high_quality"
    },

    "stable": {
        "title": "안정 생산 계약",
        "description": "수율 75% 이상 웨이퍼 8장 생산",
        "target": 8,
        "reward": 1500,
        "condition": "stable"
    },

    "volume": {
        "title": "양산 물량 계약",
        "description": "수율 50% 이상 웨이퍼 12장 생산",
        "target": 12,
        "reward": 2200,
        "condition": "volume"
    }
}


# =========================================================
# 4. 세션 상태 초기화
# =========================================================

def fresh_defaults():

    return {
        "y_data": np.zeros(150),
        "t": 0.0,

        "money": 5000,
        "stage_freq": 60,
        "tmd_freq": 60,

        "lv_sensor": 0,
        "lv_tmd": 0,
        "lv_sales": 0,

        "stage_level": 1,

        "total_wafers": 0,
        "good_wafers": 0,

        "yield_history": [],
        "production_history": [],

        "gross_revenue": 0,
        "operating_loss": 0,
        "upgrade_spend": 0,

        "last_rms": 0.0,
        "last_yield": 100.0,
        "last_money_delta": "생산 기록 없음",

        "last_wafer_grid": None,

        "contract": None,
        "contract_choice": "high_quality",

        "event_log": [
            "새로운 EUV 공장 운영을 시작했습니다."
        ],

        "bankrupt": False,

        "prev_game_active": False,
        "last_frame_ts": None,

        "batch_elapsed": 0.0,
        "frequency_elapsed": 0.0
    }


if "game_active" not in st.session_state:
    st.session_state.game_active = False

for key, value in fresh_defaults().items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 5. 보조 함수
# =========================================================

def add_event(message):

    now = datetime.now().strftime("%H:%M:%S")

    st.session_state.event_log.insert(
        0,
        f"[{now}] {message}"
    )

    st.session_state.event_log = (
        st.session_state.event_log[:10]
    )


def reset_game():

    for key, value in fresh_defaults().items():
        st.session_state[key] = value

    st.session_state.game_active = False


def adjust_tmd(delta):

    current = st.session_state.tmd_freq

    st.session_state.tmd_freq = int(
        np.clip(current + delta, 20, 120)
    )


def get_stage(total):

    if total >= 40:
        return 3

    if total >= 15:
        return 2

    return 1


def make_wafer_grid(yield_rate):

    good_count = int(
        np.clip(round(yield_rate), 0, 100)
    )

    dies = np.zeros(100, dtype=int)

    dies[:good_count] = 1

    np.random.shuffle(dies)

    return dies.reshape(10, 10)


# =========================================================
# 6. 생산 정산
# =========================================================

def settle_production(yield_rate, current_rms):

    state = st.session_state

    stage = STAGES[state.stage_level]

    reward = (
        stage["reward"]
        + state.lv_sales * 200
    )

    if yield_rate > 90:

        delta = reward

        label = f"+${reward:,} 흑자"

        state.gross_revenue += reward

        state.good_wafers += 1

    elif yield_rate > 50:

        delta = -50

        label = "-$50 수율 저하"

        state.operating_loss += 50

    else:

        delta = -200

        label = "-$200 불량 증가"

        state.operating_loss += 200

    state.money += delta

    state.total_wafers += 1

    state.yield_history.append(
        float(yield_rate)
    )

    state.yield_history = (
        state.yield_history[-100:]
    )

    state.last_rms = float(current_rms)

    state.last_yield = float(yield_rate)

    state.last_money_delta = label

    state.last_wafer_grid = make_wafer_grid(
        yield_rate
    )

    state.production_history.append({

        "웨이퍼": state.total_wafers,

        "수율(%)": round(yield_rate, 1),

        "진동 RMS(nm)": round(current_rms, 2),

        "장비(Hz)": state.stage_freq,

        "TMD(Hz)": state.tmd_freq,

        "정산 결과": label

    })

    state.production_history = (
        state.production_history[-100:]
    )

    add_event(
        f"웨이퍼 #{state.total_wafers} 생산 완료 · "
        f"수율 {yield_rate:.1f}% · {label}"
    )

    # 계약 진행
    contract = state.contract

    if contract and not contract["completed"]:

        condition = contract["condition"]

        qualifies = (

            (
                condition == "high_quality"
                and yield_rate > 90
            )

            or

            (
                condition == "stable"
                and yield_rate >= 75
            )

            or

            (
                condition == "volume"
                and yield_rate >= 50
            )

        )

        if qualifies:

            contract["progress"] += 1

            if contract["progress"] >= contract["target"]:

                contract["completed"] = True

                state.money += contract["reward"]

                add_event(
                    f"납품 계약 완료! "
                    f"${contract['reward']:,} 획득"
                )

    # 공정 단계 해금
    new_stage = get_stage(
        state.total_wafers
    )

    if new_stage > state.stage_level:

        state.stage_level = new_stage

        add_event(
            f"새 공정 해금 · {STAGES[new_stage]['name']}"
        )

    # 파산
    if state.money < 0:

        state.bankrupt = True

        state.game_active = False

        add_event("회사 파산!")


# =========================================================
# 7. 사이드바
# =========================================================

with st.sidebar:

    st.markdown("## 🏭 EUV CONTROL")

    st.caption("반도체 공장 운영 센터")

    st.markdown("---")

    st.markdown("### ⚙️ 공장 제어")

    st.toggle(
        "공장 가동 스위치",
        key="game_active",
        disabled=st.session_state.bankrupt
    )

    if st.session_state.bankrupt:

        st.error("공장 파산 상태")

    elif st.session_state.game_active:

        st.markdown(
            '<span class="status-live">'
            '● 생산 라인 가동 중</span>',
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            '<span class="status-stop">'
            '● 생산 라인 정지</span>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    st.markdown("### 🎯 TMD 주파수 조절")

    st.metric(
        "장비 발생 주파수",
        f"{st.session_state.stage_freq} Hz"
    )

    st.slider(
        "TMD 튜닝 주파수",
        min_value=20,
        max_value=120,
        step=1,
        key="tmd_freq",
        disabled=(
            not st.session_state.game_active
            or st.session_state.bankrupt
        )
    )

    b1, b2 = st.columns(2)

    with b1:

        st.button(
            "−1 Hz",
            on_click=adjust_tmd,
            args=(-1,),
            use_container_width=True,
            disabled=(
                not st.session_state.game_active
                or st.session_state.tmd_freq <= 20
            )
        )

    with b2:

        st.button(
            "+1 Hz",
            on_click=adjust_tmd,
            args=(1,),
            use_container_width=True,
            disabled=(
                not st.session_state.game_active
                or st.session_state.tmd_freq >= 120
            )
        )

    difference = abs(
        st.session_state.stage_freq
        - st.session_state.tmd_freq
    )

    st.caption(
        f"현재 주파수 오차: {difference} Hz"
    )

    st.markdown("---")

    st.markdown("### 💰 회사 자산")

    st.markdown(
        f'<div class="big-number">'
        f'${st.session_state.money:,}</div>',
        unsafe_allow_html=True
    )

    st.caption(
        f"누적 생산량: {st.session_state.total_wafers}장"
    )

    st.markdown("---")

    st.button(
        "🔄 전체 초기화",
        on_click=reset_game,
        use_container_width=True
    )

    st.caption(
        "TIP: 장비 주파수와 TMD 주파수를 "
        "가깝게 맞추면 게임상 진동이 감소합니다."
    )


# =========================================================
# 8. 실시간 물리 엔진
# =========================================================

active = (
    st.session_state.game_active
    and not st.session_state.bankrupt
)

if active:

    now = time.monotonic()

    if (
        not st.session_state.prev_game_active
        or st.session_state.last_frame_ts is None
    ):

        dt = 0.0

        st.session_state.last_frame_ts = now

        st.session_state.prev_game_active = True

    else:

        dt = max(
            0.0,
            min(
                now - st.session_state.last_frame_ts,
                0.6
            )
        )

        st.session_state.last_frame_ts = now

    st.session_state.batch_elapsed += dt

    st.session_state.frequency_elapsed += dt

    stage = STAGES[
        st.session_state.stage_level
    ]

    frequency_interval = (
        12 + st.session_state.lv_sensor * 3
    )

    tolerance = (
        5 + st.session_state.lv_tmd * 2
    )

    # 돌발 진동
    while (
        st.session_state.frequency_elapsed
        >= frequency_interval
    ):

        st.session_state.frequency_elapsed -= (
            frequency_interval
        )

        low, high = stage["freq_range"]

        old_freq = st.session_state.stage_freq

        st.session_state.stage_freq = random.randint(
            low,
            high
        )

        add_event(
            f"돌발 진동 발생 · "
            f"{old_freq}Hz → "
            f"{st.session_state.stage_freq}Hz"
        )

    # TMD 진동 감쇠 계산
    freq_diff = abs(
        st.session_state.stage_freq
        - st.session_state.tmd_freq
    )

    tuning_factor = np.exp(
        -freq_diff / tolerance
    )

    damping_ratio = max(
        0.10,
        1.0 - 0.85 * tuning_factor
    )

    # 진동 데이터
    sample_count = 12
    sample_step = 0.01

    new_t = (
        st.session_state.t
        + np.arange(sample_count) * sample_step
    )

    new_vibe = (

        15.0
        * damping_ratio
        * np.sin(
            2 * np.pi
            * st.session_state.stage_freq
            * new_t
        )

        +

        1.5
        * damping_ratio
        * np.random.randn(sample_count)

    )

    st.session_state.y_data = np.append(
        st.session_state.y_data[sample_count:],
        new_vibe
    )

    st.session_state.t += (
        sample_count * sample_step
    )

    # RMS 계산
    current_rms = float(
        np.sqrt(
            np.mean(
                st.session_state.y_data ** 2
            )
        )
    )

    # 수율 계산
    yield_rate = float(
        np.clip(
            100 - current_rms * 4.5,
            0,
            100
        )
    )

    st.session_state.last_rms = current_rms

    st.session_state.last_yield = yield_rate

    # 4초마다 생산
    while (
        st.session_state.batch_elapsed >= BATCH_INTERVAL
        and not st.session_state.bankrupt
    ):

        st.session_state.batch_elapsed -= (
            BATCH_INTERVAL
        )

        settle_production(
            yield_rate,
            current_rms
        )

else:

    st.session_state.prev_game_active = False

    st.session_state.last_frame_ts = None


# =========================================================
# 9. 메인 헤더
# =========================================================

stage = STAGES[
    st.session_state.stage_level
]

average_yield = (

    float(
        np.mean(
            st.session_state.yield_history
        )
    )

    if st.session_state.yield_history

    else 0.0

)

status_html = (

    '<span class="status-live">'
    '● LIVE · 생산 중</span>'

    if active and not st.session_state.bankrupt

    else

    '<span class="status-stop">'
    '● PAUSED · 대기 중</span>'

)

st.markdown(
    f"""
    <div class="hero">

        <div class="hero-label">
            NANO FABRICATION MANAGEMENT
        </div>

        <div class="hero-title">
            🏭 EUV 반도체 제조 타이쿤
        </div>

        <p class="hero-sub">
            TMD 진동 제어로 EUV 노광 공정을 안정화하고
            생산 수율과 회사 자산을 성장시키세요.
        </p>

        <div style="margin-top:15px;">
            {status_html}
        </div>

    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# 10. 상단 통계
# =========================================================

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "💰 회사 자산",
    f"${st.session_state.money:,}"
)

k2.metric(
    "📦 누적 생산량",
    f"{st.session_state.total_wafers}장"
)

k3.metric(
    "📈 평균 수율",
    f"{average_yield:.1f}%"
    if st.session_state.yield_history
    else "기록 없음"
)

k4.metric(
    "🏭 현재 공정 단계",
    f"Lv.{st.session_state.stage_level}"
)

if st.session_state.bankrupt:

    st.error(
        "회사가 파산했습니다. "
        "사이드바에서 전체 초기화를 눌러 다시 시작하세요."
    )


# =========================================================
# 11. 메인 탭
# =========================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 공장 대시보드",
    "📊 생산 분석",
    "🛠️ 장비 업그레이드",
    "📦 납품 계약",
    "📘 게임 안내"
])


# =========================================================
# 12. 공장 대시보드
# =========================================================

with tab1:

    left, right = st.columns(
        [1, 1],
        gap="large"
    )

    # 공정 상태
    with left:

        st.markdown(
            '<div class="section-label">'
            'PROCESS MONITOR</div>',
            unsafe_allow_html=True
        )

        st.subheader("⚙️ 실시간 공정 상태")

        a, b = st.columns(2)

        a.metric(
            "장비 주파수",
            f"{st.session_state.stage_freq} Hz"
        )

        b.metric(
            "TMD 주파수",
            f"{st.session_state.tmd_freq} Hz"
        )

        c, d = st.columns(2)

        c.metric(
            "현재 수율",
            f"{st.session_state.last_yield:.1f}%"
        )

        d.metric(
            "진동 RMS",
            f"{st.session_state.last_rms:.2f} nm"
        )

        tolerance = (
            5 + st.session_state.lv_tmd * 2
        )

        difference = abs(
            st.session_state.stage_freq
            - st.session_state.tmd_freq
        )

        st.caption(
            f"주파수 차이: {difference} Hz "
            f"· TMD 소재 허용 오차 지표: ±{tolerance} Hz"
        )

        st.progress(
            float(
                np.clip(
                    1 - difference / 100,
                    0,
                    1
                )
            )
        )

        if st.session_state.last_yield > 90:

            st.success(
                "✅ 고수율 구간입니다. 높은 생산 보상을 받을 수 있습니다."
            )

        elif st.session_state.last_yield > 50:

            st.warning(
                "⚠️ 수율 주의 구간입니다. TMD 주파수를 조절하세요."
            )

        else:

            st.error(
                "🚨 저수율 구간입니다. 진동이 크게 발생하고 있습니다."
            )

        if active:

            remaining = max(
                0,
                BATCH_INTERVAL
                - st.session_state.batch_elapsed
            )

            st.caption(
                f"다음 웨이퍼 생산까지 약 {remaining:.1f}초"
            )

            st.progress(
                float(
                    np.clip(
                        st.session_state.batch_elapsed
                        / BATCH_INTERVAL,
                        0,
                        1
                    )
                )
            )

        else:

            st.info(
                "공장을 가동하면 자동 생산이 시작됩니다."
            )

    # 웨이퍼 검사
    with right:

        st.markdown(
            '<div class="section-label">'
            'WAFER INSPECTION</div>',
            unsafe_allow_html=True
        )

        st.subheader("🔬 웨이퍼 검사 지도")

        if st.session_state.last_wafer_grid is None:

            st.info(
                "첫 번째 웨이퍼 생산이 완료되면 검사 결과가 표시됩니다."
            )

        else:

            fig, ax = plt.subplots(
                figsize=(5, 4)
            )

            fig.patch.set_facecolor("#14243a")

            ax.set_facecolor("#14243a")

            cmap = ListedColormap([
                "#ef4444",
                "#34d399"
            ])

            ax.imshow(
                st.session_state.last_wafer_grid,
                cmap=cmap,
                vmin=0,
                vmax=1,
                interpolation="nearest"
            )

            ax.set_xticks(
                np.arange(-0.5, 10, 1),
                minor=True
            )

            ax.set_yticks(
                np.arange(-0.5, 10, 1),
                minor=True
            )

            ax.grid(
                which="minor",
                color="#0b1220",
                linewidth=1.5
            )

            ax.tick_params(
                bottom=False,
                left=False,
                labelbottom=False,
                labelleft=False
            )

            for spine in ax.spines.values():
                spine.set_visible(False)

            fig.tight_layout()

            st.pyplot(
                fig,
                use_container_width=True
            )

            plt.close(fig)

            good_count = int(
                np.sum(
                    st.session_state.last_wafer_grid
                )
            )

            st.markdown(
                f"🟢 정상 칩: **{good_count}개**"
            )

            st.markdown(
                f"🔴 불량 칩: **{100-good_count}개**"
            )

    st.markdown("---")

    # 진동 파형
    wave_col, log_col = st.columns(
        [1.4, 1]
    )

    with wave_col:

        st.markdown(
            '<div class="section-label">'
            'VIBRATION SIGNAL</div>',
            unsafe_allow_html=True
        )

        st.subheader("🌊 실시간 진동 파형")

        fig, ax = plt.subplots(
            figsize=(8, 3)
        )

        fig.patch.set_facecolor("#14243a")

        ax.set_facecolor("#14243a")

        ax.plot(
            st.session_state.y_data,
            color="#38bdf8",
            linewidth=1.7
        )

        ax.axhline(
            0,
            color="#94a3b8",
            alpha=0.4
        )

        ax.set_xlabel(
            "시간 샘플",
            color="white"
        )

        ax.set_ylabel(
            "진동 진폭",
            color="white"
        )

        ax.tick_params(
            colors="white"
        )

        ax.grid(
            color="#52647d",
            alpha=0.25
        )

        for spine in ax.spines.values():

            spine.set_color("#52647d")

        fig.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)

    # 공장 알림
    with log_col:

        st.markdown(
            '<div class="section-label">'
            'FACTORY EVENT LOG</div>',
            unsafe_allow_html=True
        )

        st.subheader("📰 최근 공장 알림")

        for event in st.session_state.event_log[:7]:

            st.markdown(
                f'<div class="log-item">{event}</div>',
                unsafe_allow_html=True
            )


# =========================================================
# 13. 생산 분석
# =========================================================

with tab2:

    st.markdown(
        '<div class="section-label">'
        'PRODUCTION ANALYTICS</div>',
        unsafe_allow_html=True
    )

    st.subheader("📊 생산 실적 분석")

    total = st.session_state.total_wafers

    good = st.session_state.good_wafers

    bad = total - good

    a, b, c, d = st.columns(4)

    a.metric(
        "누적 웨이퍼",
        f"{total}장"
    )

    b.metric(
        "고수율 웨이퍼",
        f"{good}장"
    )

    c.metric(
        "고수율 미달",
        f"{bad}장"
    )

    d.metric(
        "평균 수율",
        f"{average_yield:.1f}%"
        if total
        else "기록 없음"
    )

    st.markdown("---")

    x1, x2, x3 = st.columns(3)

    x1.metric(
        "누적 매출",
        f"${st.session_state.gross_revenue:,}"
    )

    x2.metric(
        "누적 운영 손실",
        f"${st.session_state.operating_loss:,}"
    )

    x3.metric(
        "업그레이드 투자",
        f"${st.session_state.upgrade_spend:,}"
    )

    if st.session_state.production_history:

        history = pd.DataFrame(
            st.session_state.production_history
        )

        st.subheader("📈 웨이퍼별 수율 변화")

        fig, ax = plt.subplots(
            figsize=(9, 3.5)
        )

        fig.patch.set_facecolor("#14243a")

        ax.set_facecolor("#14243a")

        ax.plot(
            history["웨이퍼"],
            history["수율(%)"],
            color="#38bdf8",
            marker="o",
            markersize=4
        )

        ax.axhline(
            90,
            color="#34d399",
            linestyle="--",
            label="고수율 기준"
        )

        ax.set_ylim(0, 105)

        ax.set_xlabel(
            "웨이퍼 번호",
            color="white"
        )

        ax.set_ylabel(
            "수율 (%)",
            color="white"
        )

        ax.tick_params(
            colors="white"
        )

        ax.legend(
            facecolor="#1e293b",
            labelcolor="white"
        )

        ax.grid(
            color="#64748b",
            alpha=0.25
        )

        for spine in ax.spines.values():

            spine.set_color("#64748b")

        fig.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        plt.close(fig)

        st.subheader("📋 최근 생산 기록")

        st.dataframe(
            history.iloc[::-1].head(20),
            hide_index=True,
            use_container_width=True
        )

    else:

        st.info(
            "아직 생산 기록이 없습니다. 공장을 가동해 보세요."
        )


# =========================================================
# 14. 장비 업그레이드
# =========================================================

with tab3:

    st.markdown(
        '<div class="section-label">'
        'EQUIPMENT UPGRADE CENTER</div>',
        unsafe_allow_html=True
    )

    st.subheader("🛠️ 장비 업그레이드 상점")

    st.write(
        "공장을 정지한 상태에서 장비를 업그레이드할 수 있습니다."
    )

    upgrades = [

        {
            "key": "sensor",
            "title": "📡 정밀 센서",
            "level": st.session_state.lv_sensor,
            "cost": 2000 + st.session_state.lv_sensor * 1500,
            "description": "돌발 진동 발생 간격을 늘려 대응 시간을 확보합니다.",
            "effect": f"현재 변경 간격: {12 + st.session_state.lv_sensor * 3}초",
            "state": "lv_sensor"
        },

        {
            "key": "tmd",
            "title": "🛡️ 첨단 TMD 소재",
            "level": st.session_state.lv_tmd,
            "cost": 3000 + st.session_state.lv_tmd * 2000,
            "description": "주파수가 조금 빗나가도 진동을 더 잘 감쇠합니다.",
            "effect": f"현재 허용 오차 지표: ±{5 + st.session_state.lv_tmd * 2} Hz",
            "state": "lv_tmd"
        },

        {
            "key": "sales",
            "title": "🤝 프리미엄 계약",
            "level": st.session_state.lv_sales,
            "cost": 4000 + st.session_state.lv_sales * 3000,
            "description": "고수율 웨이퍼 생산 보상을 늘립니다.",
            "effect": f"추가 보상: +${st.session_state.lv_sales * 200:,}",
            "state": "lv_sales"
        }

    ]

    cols = st.columns(3, gap="large")

    for col, item in zip(cols, upgrades):

        with col:

            st.markdown(
                f"""
                <div class="card">

                    <div style="color:#7dd3fc;font-size:12px;font-weight:800;">
                        EQUIPMENT
                    </div>

                    <h3 style="color:#ffffff;">
                        {item['title']}
                    </h3>

                    <div class="big-number">
                        Lv.{item['level']}
                    </div>

                    <p style="color:#dbeafe;">
                        {item['description']}
                    </p>

                    <p style="color:#7dd3fc;font-weight:bold;">
                        {item['effect']}
                    </p>

                    <p style="color:#ffffff;font-weight:bold;">
                        다음 업그레이드 비용: ${item['cost']:,}
                    </p>

                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                f"업그레이드 구매 · ${item['cost']:,}",
                key=f"upgrade_{item['key']}",
                use_container_width=True,
                disabled=(
                    active
                    or st.session_state.bankrupt
                    or st.session_state.money < item["cost"]
                )
            ):

                st.session_state.money -= item["cost"]

                st.session_state.upgrade_spend += item["cost"]

                st.session_state[item["state"]] += 1

                add_event(
                    f"{item['title']} 업그레이드 완료"
                )

                st.rerun()

    if active:

        st.warning(
            "공장이 가동 중입니다. 공장을 정지한 후 구매하세요."
        )


# =========================================================
# 15. 납품 계약
# =========================================================

with tab4:

    st.markdown(
        '<div class="section-label">'
        'CUSTOMER CONTRACTS</div>',
        unsafe_allow_html=True
    )

    st.subheader("📦 납품 계약 미션")

    st.write(
        "생산 목표를 달성하고 추가 보상을 획득하세요."
    )

    contract = st.session_state.contract

    if contract and not contract["completed"]:

        st.markdown(
            f"""
            <div class="card">

                <h3 style="color:#ffffff;">
                    🎯 {contract['title']}
                </h3>

                <p style="color:#e2e8f0;">
                    {contract['description']}
                </p>

                <div class="big-number">
                    {contract['progress']} / {contract['target']}
                </div>

                <p style="color:#7dd3fc;">
                    완료 보상: ${contract['reward']:,}
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.progress(
            min(
                contract["progress"] / contract["target"],
                1.0
            )
        )

    else:

        if contract and contract["completed"]:

            st.success(
                f"이전 계약 '{contract['title']}'을 완료했습니다!"
            )

        choice = st.selectbox(
            "새로운 납품 계약 선택",
            list(CONTRACTS.keys()),
            format_func=lambda key: CONTRACTS[key]["title"],
            key="contract_choice",
            disabled=(
                active or st.session_state.bankrupt
            )
        )

        selected = CONTRACTS[choice]

        st.markdown(
            f"""
            <div class="card">

                <h3 style="color:#ffffff;">
                    {selected['title']}
                </h3>

                <p style="color:#e2e8f0;">
                    {selected['description']}
                </p>

                <div class="big-number">
                    ${selected['reward']:,}
                </div>

                <p style="color:#7dd3fc;">
                    계약 달성 보상
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "✅ 납품 계약 수락",
            disabled=(
                active or st.session_state.bankrupt
            ),
            use_container_width=True
        ):

            st.session_state.contract = {
                **selected,
                "progress": 0,
                "completed": False
            }

            add_event(
                f"새 납품 계약 수락 · {selected['title']}"
            )

            st.rerun()

    if active:

        st.info(
            "현재 공장이 가동 중입니다. "
            "진행 중인 계약은 자동으로 계산됩니다."
        )


# =========================================================
# 16. 게임 안내
# =========================================================

with tab5:

    st.markdown(
        '<div class="section-label">'
        'GAME GUIDE</div>',
        unsafe_allow_html=True
    )

    st.subheader("📘 게임 이용 방법")

    with st.container(border=True):

        st.markdown("### 1. 공장 가동")

        st.write(
            "사이드바에서 공장 가동 스위치를 켜면 "
            "EUV 공정 시뮬레이션이 시작됩니다."
        )

        st.markdown("### 2. TMD 주파수 조절")

        st.write(
            "장비 진동 주파수를 확인한 뒤 "
            "TMD 주파수를 최대한 가깝게 맞추세요."
        )

        st.markdown("### 3. 수율 관리")

        st.write(
            "진동 RMS가 낮아지면 게임상 수율이 증가합니다. "
            "높은 수율을 유지해 수익을 얻으세요."
        )

        st.markdown("### 4. 장비 업그레이드")

        st.write(
            "공장을 정지하고 상점에서 센서, TMD 소재, "
            "프리미엄 계약을 강화하세요."
        )

        st.markdown("### 5. 공정 발전")

        st.write(
            "웨이퍼 15장 생산 시 고정밀 EUV 공정, "
            "40장 생산 시 차세대 EUV 공정이 해금됩니다."
        )

    st.markdown("---")

    st.subheader("⚙️ 현재 업그레이드 효과")

    guide = pd.DataFrame({

        "장비": [
            "정밀 센서",
            "첨단 TMD 소재",
            "프리미엄 계약"
        ],

        "레벨": [
            st.session_state.lv_sensor,
            st.session_state.lv_tmd,
            st.session_state.lv_sales
        ],

        "현재 효과": [

            f"진동 변경 간격 "
            f"{12 + st.session_state.lv_sensor * 3}초",

            f"허용 오차 지표 "
            f"±{5 + st.session_state.lv_tmd * 2}Hz",

            f"고수율 추가 보상 "
            f"+${st.session_state.lv_sales * 200:,}"

        ]

    })

    st.dataframe(
        guide,
        hide_index=True,
        use_container_width=True
    )

    st.warning(
        "이 게임은 반도체 공정 이해를 위한 교육용 단순화 시뮬레이션입니다. "
        "실제 EUV 장비의 진동 제어와 수율은 훨씬 복잡한 물리적 요인에 영향을 받습니다."
    )


# =========================================================
# 17. 자동 새로고침
# =========================================================

if (
    st.session_state.game_active
    and not st.session_state.bankrupt
):

    time.sleep(FRAME_SLEEP)

    st.rerun()
