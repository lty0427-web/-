import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="EUV 진동 분석 및 TMD 제어", layout="wide")

# 세션 상태 초기화
if 'y_data' not in st.session_state:
    st.session_state.y_data = np.zeros(150)
if 't' not in st.session_state:
    st.session_state.t = 0.0

st.title("EUV 노광 장비 웨이퍼 스테이지 진동 분석")
st.write("반도체 제조 공정 중 EUV 장비의 미세 진동 데이터를 분석하고, **TMD(동조질량감쇠기)를 통한 진동 제어 시뮬레이션**을 수행합니다.")

st.sidebar.header("데이터 및 제어 설정")
data_type = st.sidebar.radio("데이터 입력 방식", ("가상 데이터 생성", "CSV 업로드"))

if data_type == "가상 데이터 생성":
    st.sidebar.subheader("가상 진동 데이터 파라미터")
    freq1 = st.sidebar.slider("주 주파수 (Hz)", 10, 200, 60)
    noise_level = st.sidebar.slider("외부 노이즈 수준", 0.0, 1.0, 0.4)
    
    st.sidebar.markdown("---")
    # 핵심 기능: TMD 제어 스위치
    tmd_active = st.sidebar.toggle("🛡️ TMD 방진 시스템 가동", value=False)
    run_live = st.sidebar.checkbox("📡 실시간 모니터링 켜기")
    
    # TMD 가동 여부에 따른 진폭 감소율 (가동 시 진폭 15%, 노이즈 30% 수준으로 억제)
    damping_factor = 0.15 if tmd_active else 1.0
    noise_damping = 0.3 if tmd_active else 1.0
    
    if run_live:
        st.subheader("실시간 진동 모니터링 및 제어 상태")
        if tmd_active:
            st.info("💡 TMD 방진 시스템 가동 중: 공진 주파수를 상쇄하여 진동을 효과적으로 억제하고 있습니다.")
        else:
            st.warning("⚠️ TMD 방진 시스템 중지: 외부 진동이 웨이퍼 스테이지에 그대로 전달되고 있습니다.")
            
        new_t = np.linspace(st.session_state.t, st.session_state.t + 0.1, 5)
        
        # TMD 댐핑 효과가 적용된 진동 계산
        new_vibe = (0.5 * damping_factor) * np.sin(2 * np.pi * freq1 * new_t) + (noise_level * noise_damping) * np.random.randn(5)
        
        st.session_state.y_data = np.append(st.session_state.y_data[5:], new_vibe)
        st.session_state.t += 0.1
        
        # 차트 출력 (진폭 변화를 한눈에 볼 수 있도록 y축 범위 고정)
        chart_data = pd.DataFrame(st.session_state.y_data, columns=["Vibration Amplitude"])
        st.line_chart(chart_data, height=400)
        
        # 실시간 상태 판정
        current_rms = np.sqrt(np.mean(st.session_state.y_data**2))
        
        col1, col2 = st.columns(2)
        col1.metric("현재 진동 RMS (실효값)", f"{current_rms:.4f}")
        
        if current_rms < 0.2:
            col2.success("상태: 매우 안정 (초정밀 노광 작업 가능)")
        elif current_rms < 0.5:
            col2.warning("상태: 주의 (진동 허용치 근접, 제품 수율 저하 우려)")
        else:
            col2.error("상태: 위험 (허용치 초과, 장비 가동 중단 권장)")
        
        time.sleep(0.05)
        st.rerun()
        
    else:
        st.session_state.y_data = np.zeros(150)
        st.session_state.t = 0.0
        
        duration = st.sidebar.slider("측정 시간 (초)", 1, 10, 5)
        sampling_rate = 1000 
        t_arr = np.linspace(0, duration, duration * sampling_rate)
        
        # 정지 화면에도 TMD 댐핑 적용
        vibration = (0.5 * damping_factor) * np.sin(2 * np.pi * freq1 * t_arr) + (noise_level * noise_damping) * np.random.randn(len(t_arr))
        df = pd.DataFrame({'Time': t_arr, 'Vibration': vibration})
        
        st.subheader("1. 정밀 진동 데이터 분석 결과")
        rms_value = np.sqrt(np.mean(df['Vibration']**2))
        max_deviation = max(abs(df['Vibration'].max()), abs(df['Vibration'].min()))
        peak_to_peak = df['Vibration'].max() - df['Vibration'].min()

        col1, col2, col3 = st.columns(3)
        col1.metric("진동 RMS", f"{rms_value:.4f}")
        col2.metric("최대 편차", f"{max_deviation:.4f}")
        col3.metric("Peak-to-Peak", f"{peak_to_peak:.4f}")

        st.subheader("2. 주파수 분석 (FFT)")
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        fig.tight_layout(pad=5.0)

        ax1.plot(df['Time'], df['Vibration'], color='royalblue' if not tmd_active else 'seagreen', linewidth=0.5)
        ax1.set_title(f"Time-Domain Signal (TMD {'ON' if tmd_active else 'OFF'})")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Amplitude")
        ax1.set_ylim(-1.5, 1.5) # 비교를 위해 y축 고정
        ax1.grid(True)

        n = len(df)
        dt = df['Time'].iloc[1] - df['Time'].iloc[0]
        yf = np.fft.fft(df['Vibration'])
        xf = np.fft.fftfreq(n, dt)[:n//2]
        
        ax2.plot(xf, 2.0/n * np.abs(yf[0:n//2]), color='crimson')
        ax2.set_title("Frequency-Domain Analysis (FFT)")
        ax2.set_xlabel("Frequency (Hz)")
        ax2.set_ylabel("Magnitude")
        ax2.set_xlim(0, 300)
        ax2.set_ylim(0, 0.6) # 비교를 위해 y축 고정
        ax2.grid(True)

        st.pyplot(fig)
