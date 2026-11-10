import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="EUV 진동 제어 시뮬레이터", layout="wide")

# 내부 메모리 초기화
if 'y_data' not in st.session_state:
    st.session_state.y_data = np.zeros(200)
if 't' not in st.session_state:
    st.session_state.t = 0.0

st.title("🔬 EUV 노광 장비 진동 모니터링 및 TMD 제어 시뮬레이터")
st.caption("초정밀 나노(nm) 공정을 위한 웨이퍼 스테이지 진동 분석 및 동조질량감쇠(TMD) 시스템")

# --- 사이드바: 환경 및 제어 설정 ---
st.sidebar.header("1. 외부 환경 (진동원)")
stage_freq = st.sidebar.slider("스테이지 발생 주파수 (Hz)", 10, 150, 60)
env_noise = st.sidebar.slider("환경 노이즈 강도", 0.0, 5.0, 1.0)

st.sidebar.header("2. TMD 방진 시스템 설정")
st.sidebar.write("실제 TMD는 고유 주파수를 맞춰야 진동이 상쇄됩니다.")
tmd_active = st.sidebar.toggle("🛡️ TMD 시스템 가동", value=False)
tmd_freq = st.sidebar.slider("TMD 튜닝 주파수 (Hz)", 10, 150, 30)
tmd_mass_ratio = st.sidebar.slider("TMD 질량비 (%)", 1, 10, 5)

st.sidebar.markdown("---")
run_mode = st.sidebar.radio("작동 모드 선택", ["📡 실시간 모니터링", "📊 정지 및 정밀 분석(FFT)"])

# --- TMD 물리 엔진 (동조 효과 계산) ---
# 스테이지 주파수와 TMD 주파수가 일치할수록(차이가 0에 가까울수록) 댐핑 효과가 극대화됨
if tmd_active:
    freq_diff = abs(stage_freq - tmd_freq)
    # 주파수 차이에 따른 상쇄 계수 (일치하면 1, 멀어지면 0)
    tuning_factor = np.exp(-freq_diff / 5.0) 
    # 질량비가 클수록, 튜닝이 잘 될수록 진동 감소 (최대 90% 감소)
    damping_ratio = 1.0 - (0.8 * tuning_factor) - (tmd_mass_ratio * 0.01)
    damping_ratio = max(0.1, damping_ratio)
else:
    damping_ratio = 1.0
    tuning_factor = 0.0

base_amplitude = 15.0 # 기준 진폭 15nm

# --- 1. 실시간 모니터링 모드 ---
if run_mode == "📡 실시간 모니터링":
    st.subheader("웨이퍼 스테이지 실시간 변위 (nm)")
    
    if tmd_active:
        if tuning_factor > 0.9:
            st.success("✅ **TMD 완벽 동조:** 고유 주파수가 일치하여 공진이 억제되고 있습니다.")
        elif tuning_factor > 0.4:
            st.warning("⚠️ **TMD 부분 동조:** 방진이 켜져 있으나 주파수가 맞지 않아 효율이 떨어집니다. 튜닝 주파수를 조절하세요.")
        else:
            st.error("🚨 **TMD 동조 실패:** 튜닝 주파수가 스테이지 주파수와 너무 달라 방진 효과가 거의 없습니다.")
    else:
        st.error("🚨 **TMD 중지:** 방진 시스템이 꺼져있어 웨이퍼 스테이지에 진동이 직접 전달됩니다.")

    # 실시간 데이터 생성
    new_t = np.linspace(st.session_state.t, st.session_state.t + 0.1, 5)
    new_vibe = (base_amplitude * damping_ratio) * np.sin(2 * np.pi * stage_freq * new_t) + (env_noise * damping_ratio) * np.random.randn(5)
    
    st.session_state.y_data = np.append(st.session_state.y_data[5:], new_vibe)
    st.session_state.t += 0.1
    
    # 그래프 출력
    chart_data = pd.DataFrame(st.session_state.y_data, columns=["Vibration (nm)"])
    st.line_chart(chart_data, height=350, use_container_width=True)
    
    # 수율(Yield) 및 RMS 계산
    current_rms = np.sqrt(np.mean(st.session_state.y_data**2))
    yield_rate = max(0, min(100, 100 - (current_rms * 4.5))) # RMS가 커지면 수율 급감
    
    col1, col2, col3 = st.columns(3)
    col1.metric("현재 진동 RMS", f"{current_rms:.2f} nm")
    col2.metric("노광 공정 예상 수율", f"{yield_rate:.1f} %")
    
    if current_rms < 3.0:
        col3.success("상태: 초정밀 노광 가능")
    elif current_rms < 8.0:
        col3.warning("상태: 오버레이 불량 주의")
    else:
        col3.error("상태: 공정 중단 및 점검")
    
    time.sleep(0.05)
    st.rerun()

# --- 2. 정밀 분석 (FFT) 모드 ---
else:
    st.session_state.y_data = np.zeros(200)
    st.session_state.t = 0.0
    
    st.subheader("정밀 주파수 및 파형 분석 (FFT)")
    st.write("실시간 데이터를 멈추고 현재 설정된 환경의 주파수 특성을 수학적으로 분석합니다.")
    
    duration = 2.0
    sampling_rate = 1000 
    t_arr = np.linspace(0, duration, int(duration * sampling_rate))
    
    # 정지 화면 데이터 계산
    vibration = (base_amplitude * damping_ratio) * np.sin(2 * np.pi * stage_freq * t_arr) + (env_noise * damping_ratio) * np.random.randn(len(t_arr))
    df = pd.DataFrame({'Time': t_arr, 'Vibration': vibration})
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.tight_layout(pad=6.0)

    # 시간 영역 파형
    line_color = 'seagreen' if (tmd_active and tuning_factor > 0.8) else 'crimson'
    ax1.plot(df['Time'], df['Vibration'], color=line_color, linewidth=0.8)
    ax1.set_title("Time-Domain Displacement (nm)", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Amplitude (nm)")
    ax1.set_ylim(-25, 25) # Y축 고정 (진폭 변화를 명확히 보기 위함)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # 주파수 영역 (FFT)
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
    
    # 피크 주파수 표시
