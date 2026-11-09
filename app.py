import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="EUV 노광 장비 진동 분석",
    page_icon="📈",
    layout="wide"
)

st.title("EUV 노광 장비 웨이퍼 스테이지 진동 분석")
st.caption("반도체 노광 장비의 진동 신호를 분석하는 교육용 프로그램")

st.info(
    "이 프로그램은 실제 EUV 장비의 측정·제어 시스템이 아닙니다. "
    "가상 데이터와 학습용 기준을 이용한 분석 프로그램입니다."
)


def make_sample_data():
    """분석 연습을 위한 가상 진동 데이터를 생성합니다."""
    time = np.arange(0, 2, 0.002)

    displacement = (
        0.025 * np.sin(2 * np.pi * 8 * time)
        + 0.008 * np.sin(2 * np.pi * 23 * time)
        + 0.003 * np.sin(2 * np.pi * 2 * time)
    )

    return pd.DataFrame({
        "time_s": time,
        "displacement_um": displacement
    })


def analyze_signal(data):
    """진동 통계와 FFT 주파수 특성을 계산합니다."""
    time = data["time_s"].to_numpy(dtype=float)
    signal = data["displacement_um"].to_numpy(dtype=float)

    if len(time) < 4:
        raise ValueError("데이터는 최소 4개 이상이어야 합니다.")

    if not np.all(np.isfinite(time)) or not np.all(np.isfinite(signal)):
        raise ValueError("데이터에 유효하지 않은 값이 있습니다.")

    intervals = np.diff(time)

    if np.any(intervals <= 0):
        raise ValueError("시간은 오름차순이어야 합니다.")

    dt = np.mean(intervals)

    if not np.allclose(intervals, dt, rtol=1e-3):
        raise ValueError("시간 간격이 일정한 데이터를 사용해 주세요.")

    centered = signal - np.mean(signal)

    rms = np.sqrt(np.mean(centered ** 2))
    maximum = np.max(np.abs(centered))
    peak_to_peak = np.max(signal) - np.min(signal)

    frequencies = np.fft.rfftfreq(len(centered), d=dt)
    amplitudes = 2 / len(centered) * np.abs(
        np.fft.rfft(centered)
    )

    amplitudes[0] = 0

    if len(centered) % 2 == 0:
        amplitudes[-1] *= 0.5

    if np.max(amplitudes) <= 1e-12:
        dominant_frequency = None
    else:
        index = np.argmax(amplitudes[1:]) + 1
        dominant_frequency = frequencies[index]

    return {
        "rms": rms,
        "maximum": maximum,
        "peak_to_peak": peak_to_peak,
        "frequency": dominant_frequency,
        "frequencies": frequencies,
        "amplitudes": amplitudes,
        "sampling_rate": 1 / dt,
        "count": len(time)
    }


st.header("1. 분석 데이터 선택")

mode = st.radio(
    "데이터 입력 방식",
    ["예시 데이터 사용", "CSV 파일 업로드"]
)

if mode == "예시 데이터 사용":
    data = make_sample_data()
    st.write("프로그램이 생성한 가상 진동 데이터를 사용합니다.")

else:
    uploaded = st.file_uploader(
        "CSV 파일을 선택하세요",
        type=["csv"]
    )

    data = None

    if uploaded is not None:
        try:
            data = pd.read_csv(uploaded)
        except Exception as error:
            st.error(f"CSV 파일을 읽지 못했습니다: {error}")


if data is not None:

    required = {"time_s", "displacement_um"}

    if not required.issubset(data.columns):
        st.error(
            "CSV 파일에는 time_s와 displacement_um 열이 필요합니다."
        )

    else:
        clean = data[["time_s", "displacement_um"]].copy()

        clean["time_s"] = pd.to_numeric(
            clean["time_s"], errors="coerce"
        )

        clean["displacement_um"] = pd.to_numeric(
            clean["displacement_um"], errors="coerce"
        )

        clean = clean.dropna()

        st.subheader("2. 진동 판정 기준 설정")

        col1, col2 = st.columns(2)

        with col1:
            caution = st.number_input(
                "주의 기준 RMS (µm)",
                min_value=0.0,
                value=0.04,
                step=0.01
            )

        with col2:
            alert = st.number_input(
                "점검 기준 RMS (µm)",
                min_value=0.0,
                value=0.08,
                step=0.01
            )

        if caution > alert:
            st.error("주의 기준은 점검 기준보다 작거나 같아야 합니다.")

        else:
            try:
                result = analyze_signal(clean)

                if result["rms"] <= caution:
                    status = "안정"
                    explanation = "설정한 주의 기준 이하입니다."

                elif result["rms"] <= alert:
                    status = "주의"
                    explanation = "주의 기준을 초과했습니다."

                else:
                    status = "점검 필요"
                    explanation = "설정한 점검 기준을 초과했습니다."

                st.header("3. 진동 분석 결과")

                st.metric("진동 상태", status)
                st.write(explanation)

                c1, c2, c3, c4 = st.columns(4)

                c1.metric("RMS", f"{result['rms']:.5f} µm")
                c2.metric("최대 편차", f"{result['maximum']:.5f} µm")
                c3.metric("최대-최소", f"{result['peak_to_peak']:.5f} µm")

                if result["frequency"] is None:
                    frequency_text = "확인되지 않음"
                else:
                    frequency_text = f"{result['frequency']:.3f} Hz"

                c4.metric("주요 주파수", frequency_text)

                st.caption(
                    f"데이터 개수: {result['count']}개 | "
                    f"샘플링 주파수: {result['sampling_rate']:.2f} Hz"
                )

                st.header("4. 진동 그래프")

                fig1, ax1 = plt.subplots()

                ax1.plot(
                    clean["time_s"],
                    clean["displacement_um"]
                )

                ax1.set_title("Vibration Signal")
                ax1.set_xlabel("Time (s)")
                ax1.set_ylabel("Displacement (µm)")
                ax1.grid(True)

                st.pyplot(fig1)
                plt.close(fig1)

                fig2, ax2 = plt.subplots()

                ax2.plot(
                    result["frequencies"],
                    result["amplitudes"]
                )

                ax2.set_title("Frequency Spectrum (FFT)")
                ax2.set_xlabel("Frequency (Hz)")
                ax2.set_ylabel("Amplitude (µm)")
                ax2.grid(True)

                st.pyplot(fig2)
                plt.close(fig2)

                st.header("5. 분석 결과 저장")

                summary = pd.DataFrame([{
                    "status": status,
                    "rms_um": result["rms"],
                    "max_deviation_um": result["maximum"],
                    "peak_to_peak_um": result["peak_to_peak"],
                    "dominant_frequency_hz": result["frequency"],
                    "sampling_rate_hz": result["sampling_rate"],
                    "sample_count": result["count"]
                }])

                st.download_button(
                    "분석 결과 CSV 다운로드",
                    data=summary.to_csv(
                        index=False
                    ).encode("utf-8-sig"),
                    file_name="vibration_result.csv",
                    mime="text/csv"
                )

            except Exception as error:
                st.error(f"분석 오류: {error}")


st.divider()

st.header("6. 프로그램의 한계")

st.write(
    "이 프로그램은 실제 EUV 장비의 센서나 제어 장치와 연결되어 있지 않습니다. "
    "가상 데이터와 사용자가 설정한 기준으로 분석하므로 "
    "실제 장비의 성능이나 안전성을 판단하는 데 사용할 수 없습니다."
)

st.caption(
    "FFT에서 가장 큰 진폭을 보이는 주파수는 주요 주파수이며, "
    "이것만으로 실제 공명이 발생했다고 확정할 수는 없습니다."
)
