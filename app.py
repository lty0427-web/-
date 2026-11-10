import random
import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.colors import ListedColormap


# ============================================================
# EUV 반도체 제조 타이쿤 | Streamlit UI 리디자인
# ============================================================

st.set_page_config(
    page_title="EUV 반도체 타이쿤",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# 1) 디자인 및 게임 설정
# -----------------------------

st.markdown(
    """
    <style>
    :root {
        --bg: #0b1220;
        --panel: #111c2e;
        --panel2: #16243a;
        --line: rgba(148, 163, 184, .18);
        --muted: #9aa9bd;
        --cyan: #38bdf8;
        --green: #34d399;
    }
    .stApp {
        background: radial-gradient(ellipse at top left, #14243c 0%, #0b1220 48%, #08101c 100%);
        color: #e5edf7;
    }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #101b2c 0%, #0c1524 100%);
        border-right: 1px solid var(--line);
    }
    .block-container { padding-top: 1.7rem; padding-bottom: 2.5rem; max-width: 1500px; }
    h1, h2, h3 { letter-spacing: -0.035em; }
    h1 { font-weight: 800 !important; }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(22,36,58,.95), rgba(14,26,43,.95));
        border: 1px solid var(--line);
        padding: 14px 16px;
        border-radius: 15px;
        box-shadow: 0 8px 24px rgba(0,0,0,.12);
    }
    [data-testid="stMetricLabel"] p { color: #aab9cc !important; font-size: .84rem !important; }
    [data-testid="stMetricValue"] { color: #f1f7ff !important; font-weight: 750; }
    [data-testid="stMetricDelta"] { font-size: .78rem !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(17, 28, 46, .72);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 14px 16px;
    }
    .hero {
        background: linear-gradient(115deg, rgba(18,39,65,.98), rgba(14,27,46,.92));
        border: 1px solid rgba(56,189,248,.24);
        border-radius: 20px;
        padding: 22px 24px;
        margin-bottom: 18px;
        box-shadow: 0 14px 38px rgba(0,0,0,.18);
    }
    .hero-kicker { color: #7dd3fc; text-transform: uppercase; letter-spacing: .13em; font-size: .72rem; font-weight: 800; }
    .hero-title { color: #f4f8ff; font-size: 1.85rem; font-weight: 850; line-height: 1.18; margin: 5px 0 8px; }
    .hero-sub { color: #b8c7d9; font-size: .94rem; margin: 0; }
    .status-pill {
        display: inline-block; border-radius: 999px; padding: 6px 11px;
        font-size: .78rem; font-weight: 750; letter-spacing: .02em;
    }
    .status-live { color: #a7f3d0; background: rgba(16,185,129,.14); border: 1px solid rgba(52,211,153,.32); }
    .status-stop { color: #cbd5e1; background: rgba(148,163,184,.12); border: 1px solid rgba(148,163,184,.22); }
    .small-note { color: #9aa9bd; font-size: .82rem; }
    .section-label { color: #7dd3fc; font-size: .73rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; margin-bottom: 3px; }
    .panel-title { color: #edf5ff; font-size: 1.08rem; font-weight: 750; margin-bottom: 4px; }
    .panel-copy { color: #9fb0c5; font-size: .86rem; }
    .big-number { color: #f8fafc; font-size: 1.7rem; font-weight: 850; }
    .divider-soft { height: 1px; background: var(--line); margin: 12px 0 16px; }
    button[kind="primary"] { border-radius: 10px; }
    .stButton button, .stDownloadButton button { border-radius: 10px; font-weight: 650; }
    [data-testid="stTabs"] button { font-weight: 650; }
    </style>
    """,
    unsafe_allow_html=True,
)

BATCH_INTERVAL = 4.0
FRAME_SLEEP = 0.25
SAMPLE_COUNT = 12
SAMPLE_STEP = 0.01

STAGES = {
    1: {
        "name": "기본 EUV 공정",
        "description": "기본 노광 공정",
        "freq_range": (30, 100),
        "reward": 300,
        "unlock_at": 0,
    },
    2: {
        "name": "고정밀 EUV 공정",
        "description": "더 넓은 주파수 범위에 대응",
        "freq_range": (25, 110),
        "reward": 420,
        "unlock_at": 15,
    },
    3: {
        "name": "차세대 EUV 공정",
        "description": "더 까다로운 진동 환경에 도전",
        "freq_range": (20, 120),
        "reward": 600,
        "unlock_at": 40,
    },
}

CONTRACTS = {
    "high_quality": {
        "title": "고수율 납품",
        "description": "수율 90% 초과 웨이퍼 5장 생산",
        "target": 5,
        "reward": 1800,
        "condition": "high_quality",
    },
    "stable": {
        "title": "안정 생산 납품",
        "description": "수율 75% 이상 웨이퍼 8장 생산",
        "target": 8,
        "reward": 1500,
        "condition": "stable",
    },
    "volume": {
        "title": "양산 물량 납품",
        "description": "수율 50% 이상 웨이퍼 12장 생산",
        "target": 12,
        "reward": 2200,
        "condition": "volume",
    },
}


# ============================================================
# 2) 게임 데이터 초기화
# ============================================================

def fresh_defaults():
    return {
        "y_data": np.zeros(150, dtype=float),
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
        "contract_reward_total": 0,

        "last_rms": 0.0,
        "last_yield": 100.0,
        "last_money_delta": "아직 생산 기록이 없습니다.",

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
        "frequency_elapsed": 0.0,
    }


if "game_active" not in st.session_state:
    st.session_state.game_active = False

for key, value in fresh_defaults().items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# 3) 게임 보조 함수
# ============================================================

def add_event(message: str):
    stamp = datetime.now().strftime("%H:%M:%S")

    st.session_state.event_log.insert(
        0,
        f"{stamp}  ·  {message}"
    )

    st.session_state.event_log = (
        st.session_state.event_log[:10]
    )


def reset_game():
    for key, value in fresh_defaults().items():
        st.session_state[key] = value

    st.session_state.game_active = False


def adjust_tmd(delta: int):
    current = int(st.session_state.tmd_freq)

    st.session_state.tmd_freq = int(
        np.clip(current + delta, 20, 120)
    )


def stage_for_wafers(total: int) -> int:
    if total >= STAGES[3]["unlock_at"]:
        return 3

    if total >= STAGES[2]["unlock_at"]:
        return 2

    return 1


def make_wafer_grid(yield_rate: float) -> np.ndarray:
    good_count = int(
        np.clip(round(yield_rate), 0, 100)
    )

    cells = np.zeros(100, dtype=int)
    cells[:good_count] = 1

    np.random.shuffle(cells)

    return cells.reshape(10, 10)


# ============================================================
# 4) 웨이퍼 생산 정산
# ============================================================

def settle_production(
    yield_rate: float,
    current_rms: float
):
    state = st.session_state

    stage = STAGES[state.stage_level]

    reward = (
        stage["reward"]
        + state.lv_sales * 200
    )

    if yield_rate > 90:

        delta = reward

        label = f"+${reward:,} · 고수율"

        state.gross_revenue += reward
        state.good_wafers += 1

    elif yield_rate > 50:

        delta = -50

        label = "-$50 · 수율 저하"

        state.operating_loss += 50

    else:

        delta = -200

        label = "-$200 · 불량 증가"

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
        "수율(%)": round(float(yield_rate), 1),
        "진동 RMS(nm)": round(float(current_rms), 2),
        "장비(Hz)": int(state.stage_freq),
        "TMD(Hz)": int(state.tmd_freq),
        "정산": label,
    })

    state.production_history = (
        state.production_history[-100:]
    )

    add_event(
        f"웨이퍼 #{state.total_wafers} 생산 · "
        f"수율 {yield_rate:.1f}% · {label}"
    )

    # 납품 계약 확인
    contract = state.contract

    if contract and not contract["completed"]:

        condition = contract["condition"]

        qualifies = (
            (
                condition == "high_quality"
                and yield_rate > 90
            )
            or (
                condition == "stable"
                and yield_rate >= 75
            )
            or (
                condition == "volume"
                and yield_rate >= 50
            )
        )

        if qualifies:

            contract["progress"] += 1

            if contract["progress"] >= contract["target"]:

                contract["completed"] = True

                state.money += contract["reward"]

                state.contract_reward_total += (
                    contract["reward"]
                )

                add_event(
                    f"계약 완료 · "
                    f"보상 ${contract['reward']:,} 획득"
                )

    # 공정 단계 해금
    new_level = stage_for_wafers(
        state.total_wafers
    )

    if new_level > state.stage_level:

        state.stage_level = new_level

        add_event(
            f"새 공정 해금 · {STAGES[new_level]['name']}"
        )

    # 파산 판정
    if state.money < 0:

        state.bankrupt = True
        state.game_active = False

        add_event(
            "회사 자산이 마이너스가 되어 파산했습니다."
        )


def metric_help():
    if st.session_state.yield_history:
        return float(
            np.mean(st.session_state.yield_history)
        )

    return 0.0


# ============================================================
# 5) 사이드바 - 조작 패널
# ============================================================

with st.sidebar:

    st.markdown("## 🏭 EUV CONTROL")

    st.caption("공장 운영 센터")

    st.markdown(
        '<div class="divider-soft"></div>',
        unsafe_allow_html=True
    )

    st.toggle(
        "공장 가동",
        key="game_active",
        disabled=st.session_state.bankrupt,
        help="가동하면 진동 시뮬레이션과 웨이퍼 생산이 시작됩니다.",
    )

    if st.session_state.bankrupt:

        st.error(
            "파산 상태 · 새 게임을 시작하세요"
        )

    elif st.session_state.game_active:

        st.markdown(
            '<span class="status-pill status-live">'
            '● 생산 라인 가동 중</span>',
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            '<span class="status-pill status-stop">'
            '● 생산 라인 정지</span>',
            unsafe_allow_html=True
        )

    st.markdown("### 🎯 TMD 튜닝")

    st.metric(
        "장비 진동 주파수",
        f"{st.session_state.stage_freq} Hz"
    )

    st.slider(
        "TMD 조절 주파수",
        min_value=20,
        max_value=120,
        step=1,
        key="tmd_freq",
        disabled=(
            not st.session_state.game_active
            or st.session_state.bankrupt
        ),
    )

    b1, b2 = st.columns(2)

    with b1:

        st.button(
            "− 1 Hz",
            key="tmd_minus",
            use_container_width=True,
            disabled=(
                not st.session_state.game_active
                or st.session_state.tmd_freq <= 20
            ),
            on_click=adjust_tmd,
            args=(-1,),
        )

    with b2:

        st.button(
            "+ 1 Hz",
            key="tmd_plus",
            use_container_width=True,
            disabled=(
                not st.session_state.game_active
                or st.session_state.tmd_freq >= 120
            ),
            on_click=adjust_tmd,
            args=(1,),
        )

    diff = abs(
        st.session_state.stage_freq
        - st.session_state.tmd_freq
    )

    st.caption(
        f"현재 주파수 오차 **{diff} Hz**"
    )

    st.markdown(
        '<div class="divider-soft"></div>',
        unsafe_allow_html=True
    )

    st.markdown("### 💳 회사 자산")

    st.markdown(
        f'<div class="big-number">'
        f'${st.session_state.money:,.0f}</div>',
        unsafe_allow_html=True
    )

    st.caption(
        f"누적 생산 {st.session_state.total_wafers:,}장"
    )

    st.button(
        "🔄 새 게임 / 전체 초기화",
        on_click=reset_game,
        use_container_width=True
    )

    st.markdown(
        '<div class="divider-soft"></div>',
        unsafe_allow_html=True
    )

    st.caption(
        "TIP · 장비 주파수와 TMD 주파수를 가깝게 "
        "맞추면 게임상 진동이 감소합니다."
    )


# ============================================================
# 6) 실시간 게임 루프
# ============================================================

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
        12.0
        + st.session_state.lv_sensor * 3.0
    )

    tolerance = (
        5.0
        + st.session_state.lv_tmd * 2.0
    )

    # 돌발 진동 발생
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
            f"돌발 진동 · "
            f"{old_freq}Hz → "
            f"{st.session_state.stage_freq}Hz"
        )

    # TMD 동조 물리 모델
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

    # 진동 파형 생성
    new_t = (
        st.session_state.t
        + np.arange(SAMPLE_COUNT) * SAMPLE_STEP
    )

    new_vibe = (
        15.0
        * damping_ratio
        * np.sin(
            2
            * np.pi
            * st.session_state.stage_freq
            * new_t
        )
        + 1.5
        * damping_ratio
        * np.random.randn(SAMPLE_COUNT)
    )

    st.session_state.y_data = np.append(
        st.session_state.y_data[SAMPLE_COUNT:],
        new_vibe
    )

    st.session_state.t += (
        SAMPLE_COUNT * SAMPLE_STEP
    )

    # RMS 계산
    current_rms = float(
        np.sqrt(
            np.mean(st.session_state.y_data ** 2)
        )
    )

    # 수율 계산
    yield_rate = float(
        np.clip(
            100.0 - current_rms * 4.5,
            0.0,
            100.0
        )
    )

    st.session_state.last_rms = current_rms
    st.session_state.last_yield = yield_rate

    # 4초마다 생산 정산
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


# ============================================================
# 7) 메인 헤더 및 KPI
# ============================================================

stage = STAGES[
    st.session_state.stage_level
]

avg_yield = metric_help()

status_html = (
    '<span class="status-pill status-live">'
    '● LIVE · 생산 중</span>'
    if active and not st.session_state.bankrupt
    else
    '<span class="status-pill status-stop">'
    '● PAUSED · 대기 중</span>'
)

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-kicker">
        NANO FABRICATION MANAGEMENT
      </div>

      <div class="hero-title">
        EUV 반도체 제조 타이쿤
      </div>

      <p class="hero-sub">
        TMD 진동 제어로 노광 공정의 안정성을 확보하고,
        생산 수율과 회사 자산을 성장시키세요.
      </p>

      <div style="margin-top:13px">
        {status_html}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "회사 자산",
    f"${st.session_state.money:,.0f}"
)

k2.metric(
    "누적 생산",
    f"{st.session_state.total_wafers:,} 장"
)

k3.metric(
    "평균 수율",
    f"{avg_yield:.1f}%"
    if st.session_state.yield_history
    else "—"
)

k4.metric(
    "현재 공정",
    f"Lv.{st.session_state.stage_level} · {stage['name']}"
)

if st.session_state.bankrupt:

    st.error(
        "회사가 파산했습니다. "
        "왼쪽 메뉴의 '새 게임 / 전체 초기화'를 눌러 "
        "다시 시작하세요."
    )


# ============================================================
# 8) 콘텐츠 탭
# ============================================================

tab_home, tab_data, tab_shop, tab_contract, tab_help = st.tabs(
    [
        "🏠 공장 대시보드",
        "📊 생산 분석",
        "🛠️ 장비 업그레이드",
        "📦 납품 계약",
        "📘 게임 안내",
    ]
)


# ============================================================
# 9) 공장 대시보드
# ============================================================

with tab_home:

    left, right = st.columns(
        [1.05, 1.0],
        gap="large"
    )

    with left:

        st.markdown(
            '<div class="section-label">'
            'PROCESS MONITOR</div>',
            unsafe_allow_html=True
        )

        st.markdown("### ⚙️ 공정 상태")

        m1, m2 = st.columns(2)

        m1.metric(
            "장비 진동",
            f"{st.session_state.stage_freq} Hz"
        )

        m2.metric(
            "TMD 설정",
            f"{st.session_state.tmd_freq} Hz"
        )

        m3, m4 = st.columns(2)

        m3.metric(
            "현재 수율",
            f"{st.session_state.last_yield:.1f}%"
        )

        m4.metric(
            "진동 RMS",
            f"{st.session_state.last_rms:.2f} nm"
        )

        tolerance_now = (
            5 + st.session_state.lv_tmd * 2
        )

        freq_error = abs(
            st.session_state.stage_freq
            - st.session_state.tmd_freq
        )

        st.caption(
            f"주파수 오차: {freq_error} Hz "
            f"· TMD 소재 허용 오차 지표: "
            f"±{tolerance_now} Hz"
        )

        st.progress(
            float(
                np.clip(
                    1.0 - freq_error / 100.0,
                    0.0,
                    1.0
                )
            )
        )

        if st.session_state.last_yield > 90:

            st.success(
                "고수율 구간 · 다음 생산 정산에서 "
                "높은 보상을 받을 수 있습니다."
            )

        elif st.session_state.last_yield > 50:

            st.warning(
                "주의 구간 · TMD 주파수를 장비 주파수에 "
                "더 가깝게 맞춰보세요."
            )

        else:

            st.error(
                "저수율 구간 · 진동이 크게 발생하고 있습니다."
            )

        if active:

            seconds_left = max(
                0.0,
                BATCH_INTERVAL
                - st.session_state.batch_elapsed
            )

            st.caption(
                f"다음 웨이퍼 정산까지 약 "
                f"{seconds_left:.1f}초"
            )

            st.progress(
                float(
                    np.clip(
                        st.session_state.batch_elapsed
                        / BATCH_INTERVAL,
                        0.0,
                        1.0
                    )
                )
            )

        else:

            st.info(
                "공장 가동 스위치를 켜면 생산과 "
                "진동 시뮬레이션이 시작됩니다."
            )

    # 웨이퍼 검사
    with right:

        st.markdown(
            '<div class="section-label">'
            'LATEST WAFER INSPECTION</div>',
            unsafe_allow_html=True
        )

        st.markdown("### 🔬 최근 웨이퍼 검사")

        if st.session_state.last_wafer_grid is None:

            st.info(
                "첫 웨이퍼가 생산되면 검사 결과가 여기에 표시됩니다."
            )

        else:

            fig, ax = plt.subplots(
                figsize=(4.2, 3.7)
            )

            fig.patch.set_facecolor("#111c2e")
            ax.set_facecolor("#111c2e")

            cmap = ListedColormap(
                ["#ef4444", "#34d399"]
            )

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
                which="both",
                bottom=False,
                left=False,
                labelbottom=False,
                labelleft=False
            )

            for spine in ax.spines.values():
                spine.set_visible(False)

            fig.tight_layout(pad=0.5)

            st.pyplot(
                fig,
                use_container_width=True
            )

            plt.close(fig)

            good_chip_count = int(
                np.sum(
                    st.session_state.last_wafer_grid
                )
            )

            st.caption(
                f"칩 검사 결과: 정상 {good_chip_count}개 "
                f"/ 불량 {100 - good_chip_count}개"
            )

    st.markdown(
        '<div class="divider-soft"></div>',
        unsafe_allow_html=True
    )

    wave_left, wave_right = st.columns(
        [1.35, 1],
        gap="large"
    )

    # 진동 그래프
    with wave_left:

        st.markdown(
            '<div class="section-label">'
            'VIBRATION SIGNAL</div>',
            unsafe_allow_html=True
        )

        st.markdown("### 🌊 실시간 진동 파형")

        wave_df = pd.DataFrame(
            {
                "진동 진폭": st.session_state.y_data
            }
        )

        st.line_chart(
            wave_df,
            height=260,
            use_container_width=True
        )

    # 공장 알림
    with wave_right:

        st.markdown(
            '<div class="section-label">'
            'FACTORY LOG</div>',
            unsafe_allow_html=True
        )

        st.markdown("### 📰 공장 알림")

        for item in st.session_state.event_log[:7]:

            st.markdown(
                f"""
                <div class='panel-copy'
                style='padding:7px 0;
                border-bottom:1px solid rgba(148,163,184,.12)'>
                    {item}
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# 10) 생산 분석
# ============================================================

with tab_data:

    st.markdown(
        '<div class="section-label">'
        'PRODUCTION ANALYTICS</div>',
        unsafe_allow_html=True
    )

    st.markdown("### 📊 생산 실적 분석")

    total = st.session_state.total_wafers

    high_yield_count = (
        st.session_state.good_wafers
    )

    below_high_yield = (
        total - high_yield_count
    )

    a, b, c, d = st.columns(4)

    a.metric(
        "누적 웨이퍼",
        f"{total:,}장"
    )

    b.metric(
        "고수율 웨이퍼",
        f"{high_yield_count:,}장"
    )

    c.metric(
        "고수율 미달",
        f"{below_high_yield:,}장"
    )

    d.metric(
        "평균 수율",
        f"{avg_yield:.1f}%"
        if total
        else "—"
    )

    r1, r2, r3 = st.columns(3)

    r1.metric(
        "생산 매출",
        f"${st.session_state.gross_revenue:,}"
    )

    r2.metric(
        "운영 손실",
        f"${st.session_state.operating_loss:,}"
    )

    r3.metric(
        "업그레이드 투자",
        f"${st.session_state.upgrade_spend:,}"
    )

    if st.session_state.yield_history:

        hist = pd.DataFrame(
            {
                "웨이퍼 번호": range(
                    1,
                    len(st.session_state.yield_history) + 1
                ),
                "수율(%)": (
                    st.session_state.yield_history
                )
            }
        )

        st.markdown("#### 웨이퍼별 수율 추이")

        st.line_chart(
            hist.set_index("웨이퍼 번호"),
            height=280,
            use_container_width=True
        )

        st.markdown("#### 최근 생산 기록")

        records = pd.DataFrame(
            st.session_state.production_history
        )

        st.dataframe(
            records.iloc[::-1].head(20),
            hide_index=True,
            use_container_width=True
        )

    else:

        st.info(
            "생산 기록이 없습니다. "
            "공장을 가동해 첫 웨이퍼를 생산하세요."
        )


# ============================================================
# 11) 장비 업그레이드
# ============================================================

with tab_shop:

    st.markdown(
        '<div class="section-label">'
        'EQUIPMENT RESEARCH & DEVELOPMENT</div>',
        unsafe_allow_html=True
    )

    st.markdown("### 🛠️ 장비 업그레이드 센터")

    st.caption(
        "공장을 정지한 상태에서 업그레이드를 구매할 수 있습니다. "
        "각 장비는 레벨이 올라갈수록 가격이 상승합니다."
    )

    upgrades = [
        {
            "key": "sensor",
            "title": "📡 정밀 센서",
            "level": st.session_state.lv_sensor,
            "cost": 2000 + st.session_state.lv_sensor * 1500,
            "desc": "돌발 진동 발생 간격을 늘려 대응 시간을 확보합니다.",
            "effect": (
                f"현재 주파수 변경 간격 · "
                f"{12 + st.session_state.lv_sensor * 3}초"
            ),
            "button": "센서 업그레이드",
            "state_key": "lv_sensor",
            "spend_key": "upgrade_spend",
        },
        {
            "key": "tmd",
            "title": "🛡️ 첨단 TMD 소재",
            "level": st.session_state.lv_tmd,
            "cost": 3000 + st.session_state.lv_tmd * 2000,
            "desc": "주파수가 조금 어긋나도 진동을 더 잘 감쇠하도록 도와줍니다.",
            "effect": (
                f"현재 허용 오차 지표 · "
                f"±{5 + st.session_state.lv_tmd * 2} Hz"
            ),
            "button": "TMD 소재 업그레이드",
            "state_key": "lv_tmd",
            "spend_key": "upgrade_spend",
        },
        {
            "key": "sales",
            "title": "🤝 프리미엄 계약",
            "level": st.session_state.lv_sales,
            "cost": 4000 + st.session_state.lv_sales * 3000,
            "desc": "고수율 웨이퍼를 생산했을 때 받는 보상을 늘립니다.",
            "effect": (
                f"웨이퍼당 추가 보상 · "
                f"+${st.session_state.lv_sales * 200:,}"
            ),
            "button": "계약 업그레이드",
            "state_key": "lv_sales",
            "spend_key": "upgrade_spend",
        },
    ]

    cols = st.columns(3, gap="medium")

    for col, upgrade in zip(cols, upgrades):

        with col:

            with st.container(border=True):

                st.markdown(
                    f"### {upgrade['title']}"
                )

                st.markdown(
                    f"<div class='big-number'>"
                    f"Lv.{upgrade['level']}</div>",
                    unsafe_allow_html=True
                )

                st.write(upgrade["desc"])

                st.caption(upgrade["effect"])

                st.markdown(
                    f"**다음 업그레이드 비용: "
                    f"${upgrade['cost']:,}**"
                )

                if st.button(
                    f"{upgrade['button']} · "
                    f"${upgrade['cost']:,}",
                    key=f"buy_{upgrade['key']}",
                    use_container_width=True,
                    disabled=(
                        active
                        or st.session_state.bankrupt
                        or st.session_state.money < upgrade["cost"]
                    ),
                ):

                    st.session_state.money -= (
                        upgrade["cost"]
                    )

                    st.session_state[
                        upgrade["spend_key"]
                    ] += upgrade["cost"]

                    st.session_state[
                        upgrade["state_key"]
                    ] += 1

                    add_event(
                        f"{upgrade['title']} 업그레이드 완료 · "
                        f"Lv.{st.session_state[upgrade['state_key']]}"
                    )

                    st.rerun()

    if active:

        st.warning(
            "공장이 가동 중입니다. "
            "사이드바의 공장 가동 스위치를 끄고 업그레이드하세요."
        )

    elif st.session_state.money < min(
        item["cost"] for item in upgrades
    ):

        st.info(
            "현재 자산으로 구매할 수 있는 업그레이드가 없을 수 있습니다. "
            "생산을 계속해 자금을 모으세요."
        )


# ============================================================
# 12) 납품 계약
# ============================================================

with tab_contract:

    st.markdown(
        '<div class="section-label">'
        'CUSTOMER ORDERS</div>',
        unsafe_allow_html=True
    )

    st.markdown("### 📦 납품 계약 및 목표")

    st.caption(
        "계약 조건에 맞는 웨이퍼를 생산하면 보너스 자산을 획득합니다. "
        "계약 수락과 교체는 공장 정지 상태에서 가능합니다."
    )

    contract = st.session_state.contract

    if contract and not contract["completed"]:

        with st.container(border=True):

            st.markdown(
                f"#### 🎯 진행 중: {contract['title']}"
            )

            st.write(contract["description"])

            progress = min(
                contract["progress"],
                contract["target"]
            )

            st.progress(
                progress / contract["target"]
            )

            c1, c2 = st.columns(2)

            c1.metric(
                "계약 진행도",
                f"{progress} / {contract['target']}"
            )

            c2.metric(
                "완료 보상",
                f"${contract['reward']:,}"
            )

    else:

        if contract and contract["completed"]:

            st.success(
                f"이전 계약 '{contract['title']}'을 완료했습니다. "
                "새 계약에 도전해 보세요!"
            )

        choice = st.selectbox(
            "새로운 계약 선택",
            options=list(CONTRACTS.keys()),
            format_func=lambda key: CONTRACTS[key]["title"],
            key="contract_choice",
            disabled=(
                active or st.session_state.bankrupt
            ),
        )

        selected = CONTRACTS[choice]

        with st.container(border=True):

            st.markdown(
                f"#### {selected['title']}"
            )

            st.write(
                selected["description"]
            )

            st.metric(
                "계약 보상",
                f"${selected['reward']:,}"
            )

            if st.button(
                "계약 수락",
                key="accept_contract",
                disabled=(
                    active or st.session_state.bankrupt
                ),
                use_container_width=True
            ):

                st.session_state.contract = {
                    **selected,
                    "progress": 0,
                    "completed": False,
                }

                add_event(
                    f"새 계약 수락 · {selected['title']}"
                )

                st.rerun()

    if active:

        st.info(
            "계약은 공장 정지 상태에서 수락할 수 있습니다. "
            "생산 중인 계약의 진행 상황은 자동으로 반영됩니다."
        )


# ============================================================
# 13) 게임 안내
# ============================================================

with tab_help:

    st.markdown(
        '<div class="section-label">'
        'HOW TO PLAY</div>',
        unsafe_allow_html=True
    )

    st.markdown("### 📘 게임 이용 안내")

    with st.container(border=True):

        st.markdown("#### 1. 공장 가동")

        st.write(
            "사이드바의 공장 가동 스위치를 켜면 "
            "진동 시뮬레이션과 생산 정산이 시작됩니다."
        )

        st.markdown("#### 2. 진동 제어")

        st.write(
            "장비 진동 주파수를 확인한 뒤 TMD 주파수를 "
            "같은 값에 가깝게 맞추세요. "
            "슬라이더 또는 ±1Hz 버튼을 사용할 수 있습니다."
        )

        st.markdown("#### 3. 생산 및 수익")

        st.write(
            "4초마다 웨이퍼 한 장이 생산됩니다. "
            "게임상 수율이 높으면 수익을 얻고, "
            "낮으면 운영 손실이 발생합니다."
        )

        st.markdown("#### 4. 공장 성장")

        st.write(
            "공장을 정지한 상태에서 장비를 업그레이드하거나 "
            "납품 계약을 선택하세요. "
            "누적 생산량 15장과 40장에 도달하면 "
            "다음 공정이 해금됩니다."
        )

    st.markdown("#### 장비 업그레이드 효과")

    guide_df = pd.DataFrame(
        [
            [
                "정밀 센서",
                "돌발 진동 발생 간격 증가",
                f"{12 + st.session_state.lv_sensor * 3}초",
            ],
            [
                "첨단 TMD 소재",
                "주파수 오차 허용 범위 증가",
                f"±{5 + st.session_state.lv_tmd * 2} Hz",
            ],
            [
                "프리미엄 계약",
                "고수율 웨이퍼 보상 증가",
                f"+${st.session_state.lv_sales * 200:,}",
            ],
        ],
        columns=[
            "장비",
            "효과",
            "현재 효과",
        ]
    )

    st.dataframe(
        guide_df,
        hide_index=True,
        use_container_width=True
    )

    st.warning(
        "교육용 단순화 모델입니다. "
        "실제 EUV 노광 장비의 진동, TMD 설계 및 반도체 수율은 "
        "이 게임보다 훨씬 다양한 요인의 영향을 받습니다."
    )


# ============================================================
# 14) 자동 새로고침
# ============================================================

if active and not st.session_state.bankrupt:

    time.sleep(FRAME_SLEEP)

    st.rerun()
