import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# 페이지 기본 설정
st.set_page_config(page_title="EUV 진동 분석", layout="wide")

st.title("EUV 노광 장비 웨이퍼 스테이지 진동 분석")
st.write("반도체 제조 공정 중 EUV 장비의 미세 진동 데이터를 분석하고 모니터링하는 시뮬레이션입니다.")

# 사이드바: 데이터 설정
st.sidebar.header("데이터 설정")
data_type = st.sidebar.radio("데이터 입력 방식", ("가상 데이터 생성", "CSV 업로드"))

if data_type == "가상 데이터 생성":
    st.sidebar.subheader("가상 진동 데이터 파라미터")
    freq1 = st.sidebar.slider("주 주파수 (Hz)", 10, 200, 60)
    noise_level = st.sidebar.slider("노이즈 수준", 0.0, 1.0, 0.2)
    
    # 애니메이션 켜기/끄기 스위치
    run_live = st.sidebar.checkbox("📡 심전도(실시간) 애니메이션 켜기")
    
    if run_live:
        st.subheader("실시간 진동 모니터링")
        st.write("웨이퍼 스테이지의 진동 파형이 실시간으로 흘러갑니다. (정지하려면 체크박스 해제)")
        
        # 애니메이션이 그려질 빈 공간 설정
        chart_placeholder = st.empty()
        status_placeholder = st.empty()
        
        # 화면에 유지할 데이터 길이 설정
        window_size = 150 
        y_data = np.zeros(window_size)
        
        t = 0
        # 체크박스가 켜져있는 동안 무한 반복 (실시간 흘러가는 효과)
        while run_live:
            # 새로운 시간과 진동 데이터 생성
            new_t = np.linspace(t, t + 0.1, 5)
            new_vibe = 0.5 * np.sin(2 * np.pi * freq1 * new_t) + noise_level * np.random.randn(5)
            
            # 기존 데이터의 맨 앞부분을 버리고, 새로운 데이터를 맨 뒤에 붙임
            y_data = np.append(y_data[5:], new_vibe)
            
            # Streamlit 내장 차트로 부드럽게 출력
            chart_placeholder.line_chart(y_data, height=400)
            
            # 실시간 RMS 상태 판정
            current_rms = np.sqrt(np.mean(y_data**2))
            if current_rms < 0.3:
                status_placeholder.success(f"상태: 안정 (현재 RMS: {current_rms:.4f}) - 노광 작업 적합")
            elif current_rms < 0.6:
                status_placeholder.warning(f"상태: 주의 (현재 RMS: {current_rms:.4f}) - 모니터링 필요")
            else:
                status_placeholder.error(f"상태: 점검 필요 (현재 RMS: {current_rms:.4f}) - 방진 시스템 확인")
                
            t += 0.1
            time.sleep(0.05) # 애니메이션 속도 조절
            
    else:
        # 애니메이션이 꺼져있을 때: 정밀 분석 모드 (FFT 등)
        duration = st.sidebar.slider("측정 시간 (초)", 1, 10, 5)
        sampling_rate = 1000 
        t_arr = np.linspace(0, duration, duration * sampling_rate)
        vibration = 0.5 * np.sin(2 * np.pi * freq1 * t_arr) + noise_level * np.random.randn(len(t_arr))
        df = pd.DataFrame({'Time': t_arr, 'Vibration': vibration})
        
        st.subheader("1. 정밀 진동 데이터 분석 결과")
        rms_value = np.sqrt(np.mean(df['Vibration']**2))
        max_deviation = max(abs(df['Vibration'].max()), abs(df['Vibration'].min()))
        peak_to_peak = df['Vibration'].max() - df['Vibration'].min()

        col1, col2, col3 = st.columns(3)
        col1.metric("진동 RMS (실효값)", f"{rms_value:.4f}")
        col2.metric("최대 편차", f"{max_deviation:.4f}")
        col3.metric("Peak-to-Peak (최대-최소)", f"{peak_to_peak:.4f}")

        st.subheader("2. 웨이퍼 스테이지 상태 판정")
        if rms_value < 0.3:
            st.success("상태: 안정 (Stable) - 정밀 노광 작업에 적합합니다.")
        elif rms_value < 0.6:
            st.warning("상태: 주의 (Warning) - 진동 허용치에 근접했습니다.")
        else:
            st.error("상태: 점검 필요 (Check) - 허용치를 초과했습니다. 방진 시스템 점검이 필요합니다.")

        st.subheader("3. 진동 데이터 시각화")
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        fig.tight_layout(pad=5.0)

        ax1.plot(df['Time'], df['Vibration'], color='royalblue', linewidth=0.5)
        ax1.set_title("Time-Domain Vibration Signal")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Amplitude")
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
        ax2.grid(True)

        st.pyplot(fig)

        st.subheader("4. 분석 데이터 다운로드")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(label="진동 데이터 CSV 다운로드", data=csv, file_name='euv_vibration_data.csv', mime='text/csv')

else:
    # CSV 업로드 시 동작
    uploaded_file = st.sidebar.file_uploader("진동 데이터 CSV 파일 업로드", type=['csv'])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.subheader("업로드된 데이터 분석 결과")
        rms_value = np.sqrt(np.mean(df['Vibration']**2))
        st.metric("진동 RMS", f"{rms_value:.4f}")
        st.line_chart(df['Vibration'])
    else:
        st.warning("CSV 파일을 업로드해주세요.")
