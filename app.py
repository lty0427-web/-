import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="EUV 진동 제어 시뮬레이터", layout="wide")

# 내부 메모리 초기화
if 'y_data' not in st.session_state:
    st.session_state.y_data = np.zeros(100)
if 't' not in st.session_state:
    st.session_state.t = 0.0

st.title("🔬 EUV 노광 공정 실시간 모니터링 및 TMD 제어")
st.caption("초정밀 나노(nm) 공정의 진동이 반도체 제조 수율에 미치는 영향 시뮬레이션")

# --- 각 수치의 의미 설명창 ---
with st.expander("💡 각 설정 수치가 반도체 제조에서 가지는 의미 알아보기 (클릭하여 펴기)"):
    st.markdown("""
    * **스테이지 발생 주파수 (Hz):** 반도체 원판(웨이퍼)을 미세하게 움직이는 장비 모터가 1초당 떨리는 횟수입니다.
    * **환경 노이즈 강도:** 반도체 클린룸 바닥, 주변 진공 펌프 등 외부 환경에서 들어오는 불규칙한 진동의 크기입니다.
    * **TMD 튜닝 주파수 (Hz):** 진동을 잡는 장치(TMD)가 목표로 삼은 주파수입니다. 발생 주파수와 동일하게 맞춰야(동조) 진동이 억제됩니다.
    * **TMD 질량비 (%):** 장비 전체 무게 대비 방진 장치의 무게 비율입니다. 수치가 클수록 진동 억제력이 강해지지만, 실제 설계 시 공간과 하중의 한계가 있습니다.
    * **진동 RMS (nm):** 현재 발생하는 진동의 평균적인 파워입니다. 수치가 낮을수록 렌즈와 웨이퍼의 정렬(Overlay)이 정확합니다.
    * **노광 공정 예상 수율 (%):** 투입된 웨이퍼 중 정상적인 반도체 칩이 만들어지는 비율입니다. 진동이 커져 초점이 빗나가면 수율이 급감합니다.
    """)

# --- 사이드바 설정 ---
st.sidebar.header("1. 외부 환경 (진동원)")
stage_freq = st.sidebar.slider("스테이지 주파수 (Hz)", 10, 150, 60, help="EUV 장비 내부 모터의 고유 진동 횟수")
env_noise = st.sidebar.slider("환경 노이즈 강도", 0.0, 5.0, 1.0, help="클린룸 바닥 등 외부에서 전달되는 진동")

st.sidebar.header("2. TMD 방진 시스템 설정")
st.sidebar.write("❗ 발생 주파수와 동일하게 맞춰야 진동이 상쇄됩니다.")
tmd_active = st.sidebar.toggle("🛡️ TMD 시스템 가동", value=False)
tmd_freq = st.sidebar.slider("TMD 튜닝 주파수 (Hz)", 10, 150, 30)
tmd_mass_ratio = st.sidebar.slider("TMD 질량비 (%)", 1, 10, 5)

st.sidebar.markdown("---")
run_mode = st.sidebar.radio("작동 모드 선택", ["📡 실시간 노광 공정 모니터링", "📊 정지 및 정밀 분석(FFT)"])

# --- TMD 물리 엔진 ---
if tmd_active:
    freq_diff = abs(stage_freq - tmd_freq)
    tuning_factor = np.exp(-freq_diff / 5.0) 
    damping_ratio = 1.0 - (0.8 * tuning_factor) - (tmd_mass_ratio * 0.01)
    damping_ratio = max(0.1, damping_ratio)
else:
    damping_ratio = 1.0
    tuning_factor = 0.0

base_amplitude = 15.0

# --- 1. 실시간 모니터링 모드 ---
if run_mode == "📡 실시간 노광 공정 모니터링":
    st.subheader("반도체 노광(Lithography) 실시간 제조 현황")
    
    # TMD 상태 메시지
    if tmd_active:
        if tuning_factor > 0.9:
            st.success("✅ **[TMD 완벽 동조]** 주파수가 일치합니다. 레이저가 웨이퍼 타겟 중앙에 정확히 맺히며 정상 제조 중입니다.")
        elif tuning_factor > 0.4:
            st.warning("⚠️ **[TMD 부분 동조]** 방진이 켜져 있으나 주파수가 안 맞습니다. 레이저 초점이 흔들리며 불량품이 발생하고 있습니다.")
        else:
            st.error("🚨 **[TMD 동조 실패]** 주파수 차이가 큽니다. 방진 효과가 없어 웨이퍼 초점을 완전히 벗어났습니다.")
    else:
        st.error("🚨 **[TMD 시스템 정지]** 방진 장치가 꺼져 있어 발생한 진동이 웨이퍼에 그대로 전달됩니다.")

    col_cam, col_wave = st.columns([1, 1])
    
    with col_cam:
        st.markdown("**📷 가상 웨이퍼 현미경 (Laser Overlay)**")
        cam_placeholder = st.empty()
    with col_wave:
        st.markdown("**🌊 스테이지 진동 파형 (Displacement)**")
        wave_placeholder = st.empty()
        
    status_placeholder = st.empty()
    
    new_t = np.linspace(st.session_state.t, st.session_state.t + 0.1, 5)
    new_vibe = (base_amplitude * damping_ratio) * np.sin(2 * np.pi * stage_freq * new_t) + (env_noise * damping_ratio) * np.random.randn(5)
    
    st.session_state.y_data = np.append(st.session_state.y_data[5:], new_vibe)
    st.session_state.t += 0.1
    
    current_rms = np.sqrt(np.mean(st.session_state.y_data**2))
    yield_rate = max(0, min(100, 100 - (current_rms * 4.5)))
    
    # --- 가상 웨이퍼 노광 시각화 (타겟과 레이저 타점) ---
    fig_cam, ax_cam = plt.subplots(figsize=(4, 4))
    ax_cam.set_facecolor('black')
    
    circle1 = plt.Circle((0, 0), 2, color='lime', fill=False, linestyle='-', linewidth=2, label="정상 범위 (Safe)")
    circle2 = plt.Circle((0, 0), 6, color='yellow', fill=False, linestyle='--', linewidth=1.5, label="주의 범위 (Warning)")
    circle3 = plt.Circle((0, 0), 12, color='red', fill=False, linestyle=':', linewidth=1.5, label="불량 범위 (Defect)")
    ax_cam.add_artist(circle1)
    ax_cam.add_artist(circle2)
    ax_cam.add_artist(circle3)
    
    # 진동 RMS 값에 비례하여 레이저 타점(파란 점)들이 사방으로 흩어짐
    scatter_x = np.random.normal(0, current_rms/1.5, 60)
    scatter_y = np.random.normal(0, current_rms/1.5, 60)
    ax_cam.scatter(scatter_x, scatter_y, color='cyan', s=15, alpha=0.8, edgecolors='white', linewidth=0.5)
    
    ax_cam.set_xlim(-15, 15)
    ax_cam.set_ylim(-15, 15)
    ax_cam.axis('off')
    
    cam_placeholder.pyplot(fig_cam)
    plt.close(fig_cam) 

    # --- 파동 차트 ---
    chart_data = pd.DataFrame(st.session_state.y_data, columns=["Vibration (nm)"])
    wave_placeholder.line_chart(chart_data, height=330, use_container_width=True)
    
    # --- 하단 지표 ---
    col1, col2, col3 = status_placeholder.columns(3)
    col1.metric("현재 진동 RMS", f"{current_rms:.2f} nm")
    col2.metric("노광 공정 예상 수율", f"{yield_rate:.1f} %")
    
    if current_rms < 3.0:
        col3.success("상태: 초정밀 노광 가능 (회로 패턴 정상)")
    elif current_rms < 8.0:
        col3.warning("상태: 오버레이 불량 주의 (회로 단선 위험)")
    else:
        col3.error("상태: 공정 중단 요망 (심각한 패턴 불량)")
    
    time.sleep(0.05)
    st.rerun()

# --- 2. 정밀 분석 (FFT) 모드 ---
else:
    st.session_state.y_data = np.zeros(100)
    st.session_state.t = 0.0
    
    st.subheader("정밀 주파수 및 파형 분석 (FFT)")
    st.write("실시간 공정 화면을 정지하고, 현재 설정된 장비의 주파수 특성을 수학적으로 분석합니다.")
    
    duration = 2.0
    sampling_rate = 1000 
    t_arr = np.linspace(0, duration, int(duration * sampling_rate))
    
    vibration = (base_amplitude * damping_ratio) * np.sin(2 * np.pi * stage_freq * t_arr) + (env_noise * damping_ratio) * np.random.randn(len(t_arr))
    df = pd.DataFrame({'Time': t_arr, 'Vibration': vibration})
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.tight_layout(pad=6.0)

    line_color = 'seagreen' if (tmd_active and tuning_factor > 0.8) else 'crimson'
    ax1.plot(df['Time'], df['Vibration'], color=line_color, linewidth=0.8)
    ax1.set_title("Time-Domain Displacement (nm)", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Amplitude (nm)")
    ax1.set_ylim(-25, 25)
    ax1.grid(True, linestyle='--', alpha=0.6)

    n = len(df)
    dt = df['Time'].iloc[1] - df['Time'].iloc[0]
    yf = np.fft.fft(df['Vibration'])
    xf = np.fft.fftfreq(n, dt)[:n//2]
    
    ax2.plot(xf, 2.0/n * np.abs(yf[0:n//2]), color='darkblue')
    ax2.set_title("Frequency-Domain Analysis (FFT)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Magnitude (nm)")
    ax2.set_xlim(0, 200)
    ax2.set_ylim(0, 16)
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    peak_freq = xf[np.argmax(2.0/n * np.abs(yf[0:n//2]))]
    ax2.axvline(x=peak_freq, color='red', linestyle=':', label=f'Peak: {peak_freq:.1f}Hz')
    ax2.legend()

    st.pyplot(fig)
