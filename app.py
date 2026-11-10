import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import random

st.set_page_config(page_title="EUV 반도체 타이쿤", layout="wide")

# --- 1. 게임 메모리(세션 상태) 초기화 ---
if 'y_data' not in st.session_state: st.session_state.y_data = np.zeros(150)
if 't' not in st.session_state: st.session_state.t = 0.0
if 'money' not in st.session_state: st.session_state.money = 5000  
if 'stage_freq' not in st.session_state: st.session_state.stage_freq = 60
if 'tick' not in st.session_state: st.session_state.tick = 0

if 'lv_sensor' not in st.session_state: st.session_state.lv_sensor = 0 
if 'lv_tmd' not in st.session_state: st.session_state.lv_tmd = 0       
if 'lv_sales' not in st.session_state: st.session_state.lv_sales = 0   

st.title("🎮 EUV 반도체 제조 타이쿤")
st.write("진동을 제어해 돈을 벌고, 공장을 멈춘 뒤 상점에서 장비를 업그레이드하세요!")

# --- 2. 상단 상태창 (항상 보임) ---
col_head1, col_head2 = st.columns([2, 1])
with col_head1:
    st.markdown(f"### 💰 현재 회사 자산: **$ {st.session_state.money:,}**")
with col_head2:
    if st.button("🔄 파산/초기화 (Reset)"):
        st.session_state.money = 5000
        st.session_state.tick = 0
        st.session_state.lv_sensor = 0
        st.session_state.lv_tmd = 0
        st.session_state.lv_sales = 0
        st.rerun()

st.markdown("---")

# --- 3. 메인 컨트롤 및 상점/게임 분기 ---
game_active = st.toggle("▶️ 공장 가동 스위치 (켜면 게임 시작 / 끄면 상점 이용)", value=False)

if not game_active:
    # 🛒 상점 모드
    st.success("⏸️ 공장이 멈췄습니다. 벌어들인 돈으로 장비를 업그레이드하세요!")
    st.subheader("🛒 EUV 장비 업그레이드 상점")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    
    with col_s1:
        st.info(f"**📡 정밀 센서 (Lv.{st.session_state.lv_sensor})**")
        st.write("돌발 진동 발생 주기를 늦춰줍니다. (플레이가 쉬워짐)")
        cost_sensor = 2000 + (st.session_state.lv_sensor * 1500)
        if st.button(f"업그레이드 (${cost_sensor:,})", key="btn_sensor"):
            if st.session_state.money >= cost_sensor:
                st.session_state.money -= cost_sensor
                st.session_state.lv_sensor += 1
                st.rerun()
            else:
                st.error("잔액 부족!")
                
    with col_s2:
        st.info(f"**🛡️ 첨단 TMD 소재 (Lv.{st.session_state.lv_tmd})**")
        st.write("주파수가 살짝 빗나가도 진동을 잘 잡아줍니다.")
        cost_tmd = 3000 + (st.session_state.lv_tmd * 2000)
        if st.button(f"업그레이드 (${cost_tmd:,})", key="btn_tmd"):
            if st.session_state.money >= cost_tmd:
                st.session_state.money -= cost_tmd
                st.session_state.lv_tmd += 1
                st.rerun()
            else:
                st.error("잔액 부족!")
                
    with col_s3:
        st.info(f"**🤝 프리미엄 계약 (Lv.{st.session_state.lv_sales})**")
        st.write("정상 수율 달성 시 한 번에 버는 돈이 증가합니다.")
        cost_sales = 4000 + (st.session_state.lv_sales * 3000)
        if st.button(f"업그레이드 (${cost_sales:,})", key="btn_sales"):
            if st.session_state.money >= cost_sales:
                st.session_state.money -= cost_sales
                st.session_state.lv_sales += 1
                st.rerun()
            else:
                st.error("잔액 부족!")

else:
    # 🏭 실시간 게임 모드
    st.session_state.tick += 1
    
    # 🕹️ 플레이어 조작반 (1단위 조작으로 변경 완료!)
    st.error(f"🚨 **현재 장비 발생 진동:** {st.session_state.stage_freq} Hz")
    tmd_freq = st.slider("🎯 TMD 튜닝 주파수 맞추기 (조작 슬라이더)", 20, 100, 60, step=1)
    
    # 상점 업그레이드 효과 적용
    freq_change_tick = 30 + (st.session_state.lv_sensor * 15) 
    tmd_tolerance = 5.0 + (st.session_state.lv_tmd * 2.0)     
    profit_base = 300 + (st.session_state.lv_sales * 200)     
    
    # 돌발 진동 발생 (1단위 랜덤 발생으로 변경하여 1단위 슬라이더의 의미를 부여함)
    if st.session_state.tick % freq_change_tick == 0:
        st.session_state.stage_freq = random.randint(30, 100)
        
    # TMD 물리 엔진 계산
    freq_diff = abs(st.session_state.stage_freq - tmd_freq)
    tuning_factor = np.exp(-freq_diff / tmd_tolerance) 
    damping_ratio = max(0.1, 1.0 - (0.85 * tuning_factor))

    # 부드러운 애니메이션
    new_t = np.linspace(st.session_state.t, st.session_state.t + 0.15, 15)
    new_vibe = (15.0 * damping_ratio) * np.sin(2 * np.pi * st.session_state.stage_freq * new_t) + (1.5 * damping_ratio) * np.random.randn(15)
    
    st.session_state.y_data = np.append(st.session_state.y_data[15:], new_vibe)
    st.session_state.t += 0.15
    
    # RMS 및 수율 계산
    current_rms = np.sqrt(np.mean(st.session_state.y_data**2))
    yield_rate = max(0, min(100, 100 - (current_rms * 4.5)))
    
    # 경제 시스템
    if yield_rate > 90:
        st.session_state.money += profit_base
        money_delta = f"+${profit_base} (흑자)"
    elif yield_rate > 50:
        st.session_state.money -= 50
        money_delta = "-$50 (수율 저하)"
    else:
        st.session_state.money -= 200
        money_delta = "-$200 (불량품)"

    # 현황판
    col1, col2 = st.columns(2)
    col1.metric("📈 실시간 수율", f"{yield_rate:.1f} %", money_delta)
    col2.metric("🌊 진동 RMS", f"{current_rms:.1f} nm")

    # 시각화 영역
    col_cam, col_wave = st.columns([1, 1])
    
    with col_cam:
        st.markdown("**📷 가상 웨이퍼 초점**")
        fig_cam, ax_cam = plt.subplots(figsize=(4, 4))
        ax_cam.set_facecolor('black')
        
        ax_cam.add_artist(plt.Circle((0, 0), 2, color='lime', fill=False, linewidth=2))
        ax_cam.add_artist(plt.Circle((0, 0), 6, color='yellow', fill=False, linestyle='--', linewidth=1.5))
        ax_cam.add_artist(plt.Circle((0, 0), 12, color='red', fill=False, linestyle=':', linewidth=1.5))
        
        scatter_x = np.random.normal(0, current_rms/1.5, 60)
        scatter_y = np.random.normal(0, current_rms/1.5, 60)
        dot_color = 'lime' if yield_rate > 90 else 'yellow' if yield_rate > 50 else 'red'
        ax_cam.scatter(scatter_x, scatter_y, color=dot_color, s=20, alpha=0.8)
        
        ax_cam.set_xlim(-15, 15)
        ax_cam.set_ylim(-15, 15)
        ax_cam.axis('off')
        st.pyplot(fig_cam)
        plt.close(fig_cam)

    with col_wave:
        st.markdown("**🌊 실시간 진동 파형**")
        chart_data = pd.DataFrame(st.session_state.y_data, columns=["Vibration"])
        st.line_chart(chart_data, height=330, use_container_width=True)
    
    if st.session_state.money < 0:
        st.error("💀 파산했습니다! 스위치를 끄고 초기화 버튼을 누르세요.")
        st.stop()

    time.sleep(0.05) 
    st.rerun()
