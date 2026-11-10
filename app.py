import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import random

st.set_page_config(page_title="EUV 반도체 타이쿤", layout="wide")

# --- 게임용 내부 메모리(세션 상태) 초기화 ---
if 'y_data' not in st.session_state:
    st.session_state.y_data = np.zeros(100)
if 't' not in st.session_state:
    st.session_state.t = 0.0
if 'money' not in st.session_state:
    st.session_state.money = 10000  # 초기 자본금 $10,000
if 'stage_freq' not in st.session_state:
    st.session_state.stage_freq = 60 # 초기 진동 주파수
if 'tick' not in st.session_state:
    st.session_state.tick = 0

st.title("🎮 EUV 반도체 제조 타이쿤 (TMD 제어 게임)")
st.write("돌발적으로 변하는 장비 진동에 맞춰 **TMD 주파수**를 조절하고, 수율을 높여 돈을 버는 게임입니다!")

# --- 게임 컨트롤 패널 (플레이어가 조작하는 곳) ---
st.markdown("### 🕹️ 플레이어 조작반")
col_control1, col_control2 = st.columns([1, 2])

with col_control1:
    game_active = st.toggle("▶️ 공장 가동 (게임 시작)", value=False)
    if st.button("🔄 파산/초기화 (Reset)"):
        st.session_state.money = 10000
        st.session_state.tick = 0
        st.session_state.stage_freq = 60
        
with col_control2:
    st.info(f"🚨 **현재 장비 발생 진동:** {st.session_state.stage_freq} Hz (여기에 맞춰 방진 시스템을 조절하세요!)")
    tmd_active = st.checkbox("🛡️ TMD 방진 시스템 켜기", value=True)
    # 모바일에서 조작하기 쉽도록 step=10 단위로 변경
    tmd_freq = st.slider("🎯 TMD 튜닝 주파수 맞추기 (조작 슬라이더)", 20, 100, 60, step=10)

st.markdown("---")

# --- 물리 엔진 및 게임 로직 ---
if tmd_active:
    freq_diff = abs(st.session_state.stage_freq - tmd_freq)
    tuning_factor = np.exp(-freq_diff / 5.0) 
    damping_ratio = max(0.1, 1.0 - (0.85 * tuning_factor))
else:
    damping_ratio = 1.0
    tuning_factor = 0.0

# --- 실시간 게임 루프 ---
if game_active:
    st.session_state.tick += 1
    
    # 약 40틱(4초)마다 진동 주파수가 무작위로 바뀜 (돌발 상황 발생!)
    if st.session_state.tick % 40 == 0:
        st.session_state.stage_freq = random.choice([30, 40, 50, 60, 70, 80, 90, 100])
        
    # 새로운 데이터 및 진동 계산
    new_t = np.linspace(st.session_state.t, st.session_state.t + 0.1, 5)
    new_vibe = (15.0 * damping_ratio) * np.sin(2 * np.pi * st.session_state.stage_freq * new_t) + (1.5 * damping_ratio) * np.random.randn(5)
    
    st.session_state.y_data = np.append(st.session_state.y_data[5:], new_vibe)
    st.session_state.t += 0.1
    
    # RMS 및 수율 계산
    current_rms = np.sqrt(np.mean(st.session_state.y_data**2))
    yield_rate = max(0, min(100, 100 - (current_rms * 4.5)))
    
    # 경제 시스템 (수율에 따른 수익/적자 계산)
    if yield_rate > 90:
        st.session_state.money += 300   # 완벽한 동조: 흑자
        money_delta = "+$300 (흑자)"
        status_color = "success"
    elif yield_rate > 50:
        st.session_state.money -= 50    # 부분 동조: 소폭 적자
        money_delta = "-$50 (수율 저하)"
        status_color = "warning"
    else:
        st.session_state.money -= 200   # 동조 실패: 심각한 적자
        money_delta = "-$200 (불량품 폐기)"
        status_color = "error"

    # --- 현황판 (대시보드) ---
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 회사 자산", f"$ {st.session_state.money:,}", money_delta)
    col2.metric("📈 노광 공정 실시간 수율", f"{yield_rate:.1f} %")
    col3.metric("🌊 현재 진동 파워 (RMS)", f"{current_rms:.1f} nm")

    # --- 가상 웨이퍼 시각화 ---
    col_cam, col_wave = st.columns([1, 1])
    
    with col_cam:
        st.markdown("**📷 가상 웨이퍼 현미경 (불량품 모니터링)**")
        fig_cam, ax_cam = plt.subplots(figsize=(4, 4))
        ax_cam.set_facecolor('black')
        
        circle1 = plt.Circle((0, 0), 2, color='lime', fill=False, linestyle='-', linewidth=2)
        circle2 = plt.Circle((0, 0), 6, color='yellow', fill=False, linestyle='--', linewidth=1.5)
        circle3 = plt.Circle((0, 0), 12, color='red', fill=False, linestyle=':', linewidth=1.5)
        ax_cam.add_artist(circle1)
        ax_cam.add_artist(circle2)
        ax_cam.add_artist(circle3)
        
        scatter_x = np.random.normal(0, current_rms/1.5, 60)
        scatter_y = np.random.normal(0, current_rms/1.5, 60)
        
        # 타점 색상도 수율에 따라 변경
        dot_color = 'lime' if yield_rate > 90 else 'yellow' if yield_rate > 50 else 'red'
        ax_cam.scatter(scatter_x, scatter_y, color=dot_color, s=20, alpha=0.8, edgecolors='white', linewidth=0.5)
        
        ax_cam.set_xlim(-15, 15)
        ax_cam.set_ylim(-15, 15)
        ax_cam.axis('off')
        st.pyplot(fig_cam)
        plt.close(fig_cam)

    with col_wave:
        st.markdown("**🌊 실시간 진동 파형**")
        chart_data = pd.DataFrame(st.session_state.y_data, columns=["Vibration (nm)"])
        st.line_chart(chart_data, height=330, use_container_width=True)
    
    if st.session_state.money < 0:
        st.error("💀 파산했습니다! 적자가 누적되어 공장 가동이 중단됩니다. 초기화 버튼을 눌러주세요.")
        st.stop()

    time.sleep(0.15) # 부드러운 게임 진행을 위한 속도 조절
    st.rerun()

else:
    # 게임이 멈춰있을 때 보여주는 기본 화면
    st.info("👆 위쪽의 **'▶️ 공장 가동 (게임 시작)'** 스위치를 켜면 반도체 생산이 시작됩니다.")
    st.metric("💰 회사 자산", f"$ {st.session_state.money:,}")
