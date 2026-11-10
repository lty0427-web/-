import random
import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.colors import ListedColormap


# ============================================================
# EUV 반도체 제조 타이쿤 - TMD 진동 제어 게임
# 생산 정산, 웨이퍼 검사, 통계, 납품 계약, 공정 단계 시스템
# ============================================================

st.set_page_config(
    page_title="EUV 반도체 타이쿤",
    page_icon="🏭",
    layout="wide",
)

# ---------------------------
# 1. 게임 설정
# ---------------------------

BATCH_INTERVAL = 4.0
FRAME_SLEEP = 0.25
WAVE_SAMPLE_COUNT = 12
WAVE_SAMPLE_STEP = 0.01

STAGES = {
    1: {
        "name": "기본 EUV 공정",
        "description": "기본적인 EUV 노광 공정을 운영합니다.",
        "freq_range": (30, 100),
        "base_reward": 300,
        "unlock_at": 0,
    },
    2: {
        "name": "고정밀 EUV 공정",
        "description": "더 넓은 주파수 범위에 대응해야 합니다.",
        "freq_range": (25, 110),
        "base_reward": 420,
        "unlock_at": 15,
    },
    3: {
        "name": "차세대 EUV 공정",
        "description": "더 까다로운 진동 환경에서 생산을 진행합니다.",
        "freq_range": (20, 120),
        "base_reward": 600,
        "unlock_at": 40,
    },
}

CONTRACTS = {
    "high_quality": {
        "title": "고수율 납품 계약",
        "description": "수율 90% 초과 웨이퍼 5장을 생산하세요.",
        "target": 5,
        "reward": 1800,
        "condition": "high_quality",
    },
    "stable": {
        "title": "안정 생산 계약",
        "description": "수율 75% 이상 웨이퍼 8장을 생산하세요.",
        "target": 8,
        "reward": 1500,
        "condition": "stable",
    },
    "volume": {
        "title": "양산 물량 계약",
        "description": "수율 50% 이상 웨이퍼 12장을 생산하세요.",
        "target": 12,
        "reward": 2200,
        "condition": "volume",
    },
}


# ---------------------------
# 2. 게임 메모리 초기화
# ---------------------------

def fresh_defaults():
    """새 게임에 필요한 세션 상태를 생성합니다."""

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

        "event_log": [
            "새로운 EUV 공장 운영을 시작했습니다."
        ],

        "bankrupt": False,

        "prev_game_active": False,
        "last_frame_ts": None,

        "batch_elapsed": 0.0,
        "frequency_elapsed": 0.0,
        "sim_elapsed": 0.0,
    }


if "game_active" not in st.session_state:
    st.session_state.game_active = False

for key, value in fresh_defaults().items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------
# 3. 게임 보조 함수
# ---------------------------

def add_event(message: str):
    """최근 게임 기록을 최대 12개까지만 보관합니다."""

    stamp = datetime.now().strftime("%H:%M:%S")

    st.session_state.event_log.insert(
        0,
        f"[{stamp}] {message}"
    )

    st.session_state.event_log = (
        st.session_state.event_log[:12]
    )


def reset_game():
    """모든 게임 진행 상황을 초기화합니다."""

    for key, value in fresh_defaults().items():
        st.session_state[key] = value

    st.session_state.game_active = False
    st.session_state.contract_choice = "high_quality"


def adjust_tmd(delta: int):
    """TMD 주파수를 1Hz 단위로 미세 조절합니다."""

    current = int(
        st.session_state.get("tmd_freq", 60)
    )

    st.session_state.tmd_freq = int(
        np.clip(current + delta, 20, 120)
    )


def get_stage_level(total_wafers: int) -> int:

    if total_wafers >= STAGES[3]["unlock_at"]:
        return 3

    if total_wafers >= STAGES[2]["unlock_at"]:
        return 2

    return 1


def make_wafer_grid(yield_rate: float) -> np.ndarray:
    """10×10 웨이퍼 칩 배열을 생성합니다."""

    good_count = int(
        np.clip(round(yield_rate), 0, 100)
    )

    dies = np.zeros(100, dtype=int)
    dies[:good_count] = 1

    np.random.shuffle(dies)

    return dies.reshape(10, 10)


# ---------------------------
# 4. 생산 정산 시스템
# ---------------------------

def settle_production(
    yield_rate: float,
    current_rms: float
):
    """웨이퍼 한 장의 생산 결과를 정산합니다."""

    state = st.session_state

    current_stage = STAGES[state.stage_level]

    profit_base = (
        current_stage["base_reward"]
        + (state.lv_sales * 200)
    )

    if yield_rate > 90:

        delta = profit_base

        label = (
            f"+${profit_base:,} (고수율 흑자)"
        )

        state.gross_revenue += profit_base
        state.good_wafers += 1

    elif yield_rate > 50:

        delta = -50

        label = "-$50 (수율 저하)"

        state.operating_loss += 50

    else:

        delta = -200

        label = "-$200 (불량률 높음)"

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

    # 생산 기록 저장
    state.production_history.append(
        {
            "웨이퍼": state.total_wafers,
            "수율(%)": round(float(yield_rate), 1),
            "진동 RMS(nm)": round(float(current_rms), 2),
            "장비 주파수(Hz)": int(state.stage_freq),
            "TMD 주파수(Hz)": int(state.tmd_freq),
            "정산 결과": label,
        }
    )

    state.production_history = (
        state.production_history[-100:]
    )

    add_event(
        f"웨이퍼 #{state.total_wafers} 생산 완료 · "
        f"수율 {yield_rate:.1f}% · {label}"
    )

    # 납품 계약 진행 상황 확인
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
                    f"계약 달성! 보상 "
                    f"${contract['reward']:,}을 획득했습니다."
                )

    # 공정 단계 해금
    new_stage_level = get_stage_level(
        state.total_wafers
    )

    if new_stage_level > state.stage_level:

        state.stage_level = new_stage_level

        unlocked = STAGES[new_stage_level]

        add_event(
            f"공정 단계 해금: {unlocked['name']}"
        )

    # 파산 판정
    if state.money < 0:

        state.bankrupt = True

        add_event(
            "자산이 0 미만이 되어 공장이 파산했습니다."
        )


# ============================================================
# 5. 상단 화면 및 회사 현황
# ============================================================

st.title("🏭 EUV 반도체 제조 타이쿤")

st.caption(
    "TMD 주파수를 조절해 진동을 줄이고, "
    "웨이퍼 수율을 높여 회사를 성장시키세요."
)

head_left, head_right = st.columns([3, 1])

with head_left:

    st.markdown(
        f"### 💰 회사 자산: **${st.session_state.money:,.0f}**"
    )

with head_right:

    st.button(
        "🔄 새 게임 / 초기화",
        on_click=reset_game,
        use_container_width=True,
        help="자산, 업그레이드, 생산 기록을 모두 초기화합니다.",
    )


stage_level_now = get_stage_level(
    st.session_state.total_wafers
)

st.session_state.stage_level = max(
    st.session_state.stage_level,
    stage_level_now
)

current_stage = STAGES[
    st.session_state.stage_level
]

avg_yield = (
    float(np.mean(st.session_state.yield_history))
    if st.session_state.yield_history
    else 0.0
)


metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "공정 단계",
    f"Lv.{st.session_state.stage_level} · {current_stage['name']}"
)

metric2.metric(
    "누적 웨이퍼",
    f"{st.session_state.total_wafers:,}장"
)

metric3.metric(
    "평균 수율",
    f"{avg_yield:.1f}%"
    if st.session_state.yield_history
    else "-"
)

metric4.metric(
    "정상 수율 웨이퍼",
    f"{st.session_state.good_wafers:,}장"
)

st.markdown("---")


# ============================================================
# 6. 공장 가동 스위치
# ============================================================

if st.session_state.bankrupt:

    st.session_state.game_active = False

game_active = st.toggle(
    "▶️ 공장 가동 스위치 "
    "(켜면 생산 시작 / 끄면 상점과 계약 이용)",
    key="game_active",
    disabled=st.session_state.bankrupt,
)


# ============================================================
# 7. 게임 시간 및 물리 엔진
# ============================================================

if game_active and not st.session_state.bankrupt:

    now = time.monotonic()

    # 공장을 새로 켰을 때 정지 시간 제외
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

    st.session_state.sim_elapsed += dt

    st.session_state.batch_elapsed += dt

    st.session_state.frequency_elapsed += dt

    # 정밀 센서 업그레이드 효과
    frequency_change_interval = (
        12.0 + (st.session_state.lv_sensor * 3.0)
    )

    # TMD 소재 업그레이드 효과
    tolerance = (
        5.0 + (st.session_state.lv_tmd * 2.0)
    )

    # 돌발 진동 발생
    while (
        st.session_state.frequency_elapsed
        >= frequency_change_interval
    ):

        st.session_state.frequency_elapsed -= (
            frequency_change_interval
        )

        low_freq, high_freq = (
            current_stage["freq_range"]
        )

        previous_freq = st.session_state.stage_freq

        new_freq = random.randint(
            low_freq,
            high_freq
        )

        st.session_state.stage_freq = new_freq

        add_event(
            f"돌발 진동 발생: "
            f"{previous_freq}Hz → {new_freq}Hz"
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
        1.0 - (0.85 * tuning_factor)
    )

    # 파동 생성
    new_t = (
        st.session_state.t
        + np.arange(WAVE_SAMPLE_COUNT)
        * WAVE_SAMPLE_STEP
    )

    new_vibe = (
        (15.0 * damping_ratio)
        * np.sin(
            2 * np.pi
            * st.session_state.stage_freq
            * new_t
        )
        + (1.5 * damping_ratio)
        * np.random.randn(WAVE_SAMPLE_COUNT)
    )

    st.session_state.y_data = np.append(
        st.session_state.y_data[WAVE_SAMPLE_COUNT:],
        new_vibe
    )

    st.session_state.t += (
        WAVE_SAMPLE_COUNT * WAVE_SAMPLE_STEP
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
            100.0 - (current_rms * 4.5),
            0.0,
            100.0
        )
    )

    st.session_state.last_rms = current_rms

    st.session_state.last_yield = yield_rate

    # 4초마다 웨이퍼 한 장 생산
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

        current_stage = STAGES[
            st.session_state.stage_level
        ]

    next_batch = max(
        0.0,
        BATCH_INTERVAL
        - st.session_state.batch_elapsed
    )

else:

    # 공장 정지 시 시간 정지
    st.session_state.prev_game_active = False

    st.session_state.last_frame_ts = None

    next_batch = (
        BATCH_INTERVAL
        - st.session_state.batch_elapsed
    )


# ============================================================
# 8. 화면 탭
# ============================================================

tab_factory, tab_stats, tab_shop, tab_contract, tab_guide = (
    st.tabs(
        [
            "🏭 생산 현황",
            "📊 생산 통계",
            "🛒 장비 업그레이드",
            "📦 납품 계약",
            "📘 게임 안내",
        ]
    )
)


# ============================================================
# 9. 생산 현황
# ============================================================

with tab_factory:

    if st.session_state.bankrupt:

        st.error(
            "💸 파산했습니다. "
            "새 게임 / 초기화 버튼을 눌러 다시 시작하세요."
        )

    elif game_active:

        st.success(
            f"공장 가동 중 · {current_stage['name']}"
        )

    else:

        st.info(
            "공장이 정지되어 있습니다. "
            "가동 스위치를 켜면 생산이 시작됩니다."
        )

    control_col, status_col = st.columns([1.05, 1])

    # ---------------------------
    # TMD 조작반
    # ---------------------------

    with control_col:

        st.subheader("🎯 TMD 진동 제어")

        low_freq, high_freq = (
            current_stage["freq_range"]
        )

        st.metric(
            "현재 장비 진동 주파수",
            f"{st.session_state.stage_freq} Hz"
        )

        st.slider(
            "TMD 튜닝 주파수",
            min_value=20,
            max_value=120,
            step=1,
            key="tmd_freq",
            disabled=(
                not game_active
                or st.session_state.bankrupt
            ),
            help=(
                "장비 주파수에 가까울수록 "
                "게임 모델에서 진동이 더 많이 감쇠됩니다."
            ),
        )

        fine1, fine2, fine3 = st.columns([1, 1, 2])

        with fine1:

            st.button(
                "−1 Hz",
                on_click=adjust_tmd,
                args=(-1,),
                disabled=(
                    not game_active
                    or st.session_state.tmd_freq <= 20
                ),
                use_container_width=True,
            )

        with fine2:

            st.button(
                "+1 Hz",
                on_click=adjust_tmd,
                args=(1,),
                disabled=(
                    not game_active
                    or st.session_state.tmd_freq >= 120
                ),
                use_container_width=True,
            )

        with fine3:

            st.caption(
                "슬라이더 또는 버튼으로 1Hz 단위 조절"
            )

        current_diff = abs(
            st.session_state.stage_freq
            - st.session_state.tmd_freq
        )

        tolerance_now = (
            5.0 + (st.session_state.lv_tmd * 2.0)
        )

        st.metric(
            "주파수 오차",
            f"{current_diff} Hz",
            delta=(
                f"TMD 허용 범위 기준 ±{tolerance_now:.0f} Hz"
            ),
            delta_color="off",
        )

        st.progress(
            float(
                np.clip(
                    1.0 - current_diff / 100.0,
                    0.0,
                    1.0
                )
            )
        )

        if game_active:

            st.caption(
                f"다음 웨이퍼 정산까지 약 "
                f"{next_batch:.1f}초"
            )

        else:

            st.caption(
                "공장을 가동하면 생산 정산 타이머가 시작됩니다."
            )

    # ---------------------------
    # 공정 상태판
    # ---------------------------

    with status_col:

        st.subheader("📈 실시간 공정 상태")

        status1, status2 = st.columns(2)

        status1.metric(
            "현재 수율",
            f"{st.session_state.last_yield:.1f}%"
        )

        status2.metric(
            "진동 RMS",
            f"{st.session_state.last_rms:.2f} nm"
        )

        st.metric(
            "최근 정산",
            st.session_state.last_money_delta
        )

        if st.session_state.last_yield > 90:

            st.success(
                "✅ 고수율 구간: 정상 생산 보상을 받을 수 있습니다."
            )

        elif st.session_state.last_yield > 50:

            st.warning(
                "⚠️ 주의 구간: TMD 주파수를 더 정확하게 맞춰보세요."
            )

        else:

            st.error(
                "🚨 저수율 구간: 진동이 커서 불량품이 증가하고 있습니다."
            )

    st.markdown("---")

    wafer_col, wave_col = st.columns(2)

    # ========================================================
    # 웨이퍼 검사 시스템
    # ========================================================

    with wafer_col:

        st.subheader("🔬 최근 웨이퍼 검사 지도")

        st.caption(
            "10×10 칩 배열 · 초록색: 정상 칩 · 빨간색: 불량 칩"
        )

        if st.session_state.last_wafer_grid is None:

            st.info(
                "첫 웨이퍼가 생산되면 검사 결과가 여기에 표시됩니다."
            )

        else:

            fig_wafer, ax_wafer = plt.subplots(
                figsize=(4.2, 4.2)
            )

            cmap = ListedColormap(
                ["#ef4444", "#22c55e"]
            )

            ax_wafer.imshow(
                st.session_state.last_wafer_grid,
                cmap=cmap,
                vmin=0,
                vmax=1,
                interpolation="nearest",
            )

            ax_wafer.set_xticks(
                np.arange(-0.5, 10, 1),
                minor=True
            )

            ax_wafer.set_yticks(
                np.arange(-0.5, 10, 1),
                minor=True
            )

            ax_wafer.grid(
                which="minor",
                color="white",
                linewidth=1.2
            )

            ax_wafer.tick_params(
                which="both",
                bottom=False,
                left=False,
                labelbottom=False,
                labelleft=False
            )

            for spine in ax_wafer.spines.values():

                spine.set_visible(False)

            fig_wafer.tight_layout(pad=0.2)

            st.pyplot(
                fig_wafer,
                use_container_width=True
            )

            plt.close(fig_wafer)

            good_die_count = int(
                np.sum(
                    st.session_state.last_wafer_grid
                )
            )

            st.caption(
                f"최근 웨이퍼 정상 칩 "
                f"{good_die_count}/100개"
            )

        # -----------------------
        # 레이저 초점 시각화
        # -----------------------

        st.markdown(
            "#### 🎯 실시간 레이저 초점 분산"
        )

        focus_spread = max(
            st.session_state.last_rms / 1.5,
            0.25
        )

        scatter_x = np.random.normal(
            0,
            focus_spread,
            60
        )

        scatter_y = np.random.normal(
            0,
            focus_spread,
            60
        )

        focus_color = (
            "#22c55e"
            if st.session_state.last_yield > 90
            else "#facc15"
            if st.session_state.last_yield > 50
            else "#ef4444"
        )

        fig_focus, ax_focus = plt.subplots(
            figsize=(4.2, 3.5)
        )

        ax_focus.set_facecolor("#111827")

        ax_focus.add_artist(
            plt.Circle(
                (0, 0),
                2,
                color="#22c55e",
                fill=False,
                linewidth=2
            )
        )

        ax_focus.add_artist(
            plt.Circle(
                (0, 0),
                6,
                color="#facc15",
                fill=False,
                linestyle="--",
                linewidth=1.4
            )
        )

        ax_focus.add_artist(
            plt.Circle(
                (0, 0),
                12,
                color="#ef4444",
                fill=False,
                linestyle=":",
                linewidth=1.4
            )
        )

        ax_focus.scatter(
            scatter_x,
            scatter_y,
            color=focus_color,
            s=17,
            alpha=0.8
        )

        ax_focus.set_xlim(-15, 15)
        ax_focus.set_ylim(-15, 15)

        ax_focus.set_aspect("equal")

        ax_focus.axis("off")

        fig_focus.tight_layout(pad=0.2)

        st.pyplot(
            fig_focus,
            use_container_width=True
        )

        plt.close(fig_focus)

    # ========================================================
    # 실시간 진동 그래프
    # ========================================================

    with wave_col:

        st.subheader("🌊 실시간 진동 파형")

        wave_df = pd.DataFrame(
            {
                "진동 진폭": st.session_state.y_data
            }
        )

        st.line_chart(
            wave_df,
            height=300,
            use_container_width=True
        )

        st.caption(
            "TMD를 장비 주파수에 맞추면 "
            "게임 모델의 진동 진폭이 작아집니다."
        )

    # ---------------------------
    # 공장 알림
    # ---------------------------

    st.markdown("---")

    st.subheader("📰 최근 공장 알림")

    for event in st.session_state.event_log[:5]:

        st.write(f"• {event}")


# ============================================================
# 10. 생산 통계
# ============================================================

with tab_stats:

    st.subheader("📊 생산 실적 대시보드")

    total = st.session_state.total_wafers

    good = st.session_state.good_wafers

    defective = total - good

    current_average = avg_yield

    s1, s2, s3, s4 = st.columns(4)

    s1.metric(
        "누적 생산량",
        f"{total:,}장"
    )

    s2.metric(
        "고수율 웨이퍼",
        f"{good:,}장"
    )

    s3.metric(
        "고수율 미달 웨이퍼",
        f"{defective:,}장"
    )

    s4.metric(
        "누적 평균 수율",
        f"{current_average:.1f}%"
        if total
        else "-"
    )

    finance1, finance2, finance3 = st.columns(3)

    finance1.metric(
        "생산 매출 누계",
        f"${st.session_state.gross_revenue:,}"
    )

    finance2.metric(
        "운영 손실 누계",
        f"${st.session_state.operating_loss:,}"
    )

    finance3.metric(
        "업그레이드 투자",
        f"${st.session_state.upgrade_spend:,}"
    )

    if st.session_state.production_history:

        history_df = pd.DataFrame(
            st.session_state.production_history
        )

        st.markdown(
            "#### 웨이퍼별 수율 추이"
        )

        yield_chart = history_df.set_index(
            "웨이퍼"
        )[["수율(%)"]]

        st.line_chart(
            yield_chart,
            height=260,
            use_container_width=True
        )

        st.markdown(
            "#### 최근 생산 기록"
        )

        st.dataframe(
            history_df.tail(15).iloc[::-1],
            hide_index=True,
            use_container_width=True,
        )

    else:

        st.info(
            "아직 생산 기록이 없습니다. "
            "공장을 가동해 첫 웨이퍼를 생산하세요."
        )


# ============================================================
# 11. 장비 업그레이드 상점
# ============================================================

with tab_shop:

    st.subheader(
        "🛒 EUV 장비 업그레이드 상점"
    )

    if game_active:

        st.info(
            "업그레이드는 공장을 정지한 상태에서 구매할 수 있습니다. "
            "가동 스위치를 끄세요."
        )

    col_sensor, col_tmd, col_sales = st.columns(3)

    cost_sensor = (
        2000
        + (st.session_state.lv_sensor * 1500)
    )

    cost_tmd = (
        3000
        + (st.session_state.lv_tmd * 2000)
    )

    cost_sales = (
        4000
        + (st.session_state.lv_sales * 3000)
    )

    # ---------------------------
    # 정밀 센서
    # ---------------------------

    with col_sensor:

        st.markdown(
            f"### 📡 정밀 센서 · Lv.{st.session_state.lv_sensor}"
        )

        st.write(
            "돌발 진동 발생 간격을 늘려 "
            "주파수 변화에 대응할 시간을 확보합니다."
        )

        st.caption(
            f"현재 효과: 약 "
            f"{12 + st.session_state.lv_sensor * 3}초마다 주파수 변화"
        )

        st.write(
            f"다음 업그레이드 비용: **${cost_sensor:,}**"
        )

        if st.button(
            f"정밀 센서 업그레이드 (${cost_sensor:,})",
            key="buy_sensor",
            disabled=(
                game_active
                or st.session_state.money < cost_sensor
                or st.session_state.bankrupt
            ),
            use_container_width=True,
        ):

            st.session_state.money -= cost_sensor

            st.session_state.upgrade_spend += cost_sensor

            st.session_state.lv_sensor += 1

            add_event(
                f"정밀 센서가 Lv.{st.session_state.lv_sensor}(으)로 업그레이드되었습니다."
            )

            st.rerun()

    # ---------------------------
    # 첨단 TMD 소재
    # ---------------------------

    with col_tmd:

        st.markdown(
            f"### 🛡️ 첨단 TMD 소재 · Lv.{st.session_state.lv_tmd}"
        )

        st.write(
            "장비와 TMD 주파수가 조금 어긋나도 "
            "진동을 더 잘 감쇠하도록 도와줍니다."
        )

        st.caption(
            f"현재 허용 오차: "
            f"±{5 + st.session_state.lv_tmd * 2}Hz"
        )

        st.write(
            f"다음 업그레이드 비용: **${cost_tmd:,}**"
        )

        if st.button(
            f"TMD 소재 업그레이드 (${cost_tmd:,})",
            key="buy_tmd",
            disabled=(
                game_active
                or st.session_state.money < cost_tmd
                or st.session_state.bankrupt
            ),
            use_container_width=True,
        ):

            st.session_state.money -= cost_tmd

            st.session_state.upgrade_spend += cost_tmd

            st.session_state.lv_tmd += 1

            add_event(
                f"첨단 TMD 소재가 Lv.{st.session_state.lv_tmd}(으)로 업그레이드되었습니다."
            )

            st.rerun()

    # ---------------------------
    # 프리미엄 계약
    # ---------------------------

    with col_sales:

        st.markdown(
            f"### 🤝 프리미엄 계약 · Lv.{st.session_state.lv_sales}"
        )

        st.write(
            "고수율 웨이퍼 생산 시 받는 "
            "기본 생산 보상을 늘립니다."
        )

        st.caption(
            f"현재 추가 보상: 웨이퍼당 "
            f"+${st.session_state.lv_sales * 200:,}"
        )

        st.write(
            f"다음 업그레이드 비용: **${cost_sales:,}**"
        )

        if st.button(
            f"프리미엄 계약 업그레이드 (${cost_sales:,})",
            key="buy_sales",
            disabled=(
                game_active
                or st.session_state.money < cost_sales
                or st.session_state.bankrupt
            ),
            use_container_width=True,
        ):

            st.session_state.money -= cost_sales

            st.session_state.upgrade_spend += cost_sales

            st.session_state.lv_sales += 1

            add_event(
                f"프리미엄 계약이 Lv.{st.session_state.lv_sales}(으)로 업그레이드되었습니다."
            )

            st.rerun()

    # 구매 가능한 업그레이드 표시
    if not game_active and not st.session_state.bankrupt:

        affordable = sum(
            [
                st.session_state.money >= cost_sensor,
                st.session_state.money >= cost_tmd,
                st.session_state.money >= cost_sales,
            ]
        )

        st.caption(
            f"현재 자산으로 구매할 수 있는 업그레이드: "
            f"{affordable}종"
        )


# ============================================================
# 12. 납품 계약 미션
# ============================================================

with tab_contract:

    st.subheader(
        "📦 생산 목표 및 납품 계약"
    )

    st.write(
        "계약 조건을 달성하면 추가 보상을 받습니다. "
        "한 번에 하나의 계약만 진행할 수 있습니다."
    )

    active_contract = st.session_state.contract

    if active_contract and not active_contract["completed"]:

        st.info(
            "현재 진행 중인 계약"
        )

        st.markdown(
            f"### {active_contract['title']}"
        )

        st.write(
            active_contract["description"]
        )

        progress = min(
            active_contract["progress"],
            active_contract["target"]
        )

        st.progress(
            progress / active_contract["target"]
        )

        st.write(
            f"진행도: **{progress}/{active_contract['target']}** · "
            f"완료 보상: **${active_contract['reward']:,}**"
        )

    else:

        if active_contract and active_contract["completed"]:

            st.success(
                f"이전 계약 '{active_contract['title']}'을 완료했습니다. "
                "새로운 계약을 선택할 수 있습니다."
            )

        selected_key = st.selectbox(
            "수락할 계약 선택",
            options=list(CONTRACTS.keys()),
            format_func=lambda key: CONTRACTS[key]["title"],
            key="contract_choice",
            disabled=(
                game_active
                or st.session_state.bankrupt
            ),
        )

        selected_contract = CONTRACTS[selected_key]

        st.write(
            selected_contract["description"]
        )

        st.metric(
            "계약 완료 보상",
            f"${selected_contract['reward']:,}"
        )

        if st.button(
            "계약 수락",
            disabled=(
                game_active
                or st.session_state.bankrupt
            ),
            use_container_width=True,
        ):

            st.session_state.contract = {
                **selected_contract,
                "progress": 0,
                "completed": False,
            }

            add_event(
                f"새 계약 수락: {selected_contract['title']}"
            )

            st.rerun()

    if game_active:

        st.caption(
            "계약 수락 및 변경은 공장을 정지한 상태에서 할 수 있습니다."
        )


# ============================================================
# 13. 게임 안내
# ============================================================

with tab_guide:

    st.subheader(
        "📘 게임 방법"
    )

    st.markdown(
        """
        1. **공장 가동** 스위치를 켜면 진동 시뮬레이션이 시작됩니다.

        2. **장비 발생 주파수**를 확인하고 TMD 슬라이더를
           같은 값에 가깝게 조절합니다.

        3. 진동 RMS가 낮아질수록 게임의 **가상 수율**이 올라갑니다.

        4. **4초마다 웨이퍼 1장**의 생산 결과가 정산됩니다.

        5. 공장을 정지하면 상점에서 장비를 업그레이드하거나
           납품 계약을 수락할 수 있습니다.

        6. 누적 생산량 15장, 40장에 도달하면
           다음 공정 단계가 해금됩니다.
        """
    )

    st.markdown(
        "#### 업그레이드 효과"
    )

    st.write(
        f"- 정밀 센서 Lv.{st.session_state.lv_sensor}: "
        f"주파수 변화 간격 "
        f"{12 + st.session_state.lv_sensor * 3}초"
    )

    st.write(
        f"- 첨단 TMD 소재 Lv.{st.session_state.lv_tmd}: "
        f"주파수 허용 오차 "
        f"±{5 + st.session_state.lv_tmd * 2}Hz"
    )

    st.write(
        f"- 프리미엄 계약 Lv.{st.session_state.lv_sales}: "
        f"고수율 생산 추가 보상 "
        f"+${st.session_state.lv_sales * 200:,}"
    )

    st.markdown(
        "#### 공정 단계"
    )

    for level, stage in STAGES.items():

        is_unlocked = (
            st.session_state.total_wafers
            >= stage["unlock_at"]
        )

        status = (
            "해금"
            if is_unlocked
            else f"웨이퍼 {stage['unlock_at']}장 생산 시 해금"
        )

        st.write(
            f"- **Lv.{level} {stage['name']}** — "
            f"주파수 범위 "
            f"{stage['freq_range'][0]}~"
            f"{stage['freq_range'][1]}Hz · {status}"
        )

    st.warning(
        "참고: 진동 감쇠와 수율 계산은 게임 플레이를 위한 "
        "단순화된 교육용 모델입니다. 실제 EUV 노광 장비의 진동, "
        "TMD 설계 및 반도체 수율은 훨씬 다양한 요인의 영향을 받습니다."
    )


# ============================================================
# 14. 실시간 게임 반복
# ============================================================

if game_active and not st.session_state.bankrupt:

    time.sleep(FRAME_SLEEP)

    st.rerun()
