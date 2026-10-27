"""PeakGuard 데모 앱 — 다음 날 피크 예측 + 기본요금 절감 시뮬레이션.

Emergent 'World's Biggest Business Competition' App Builder 트랙 출품용 데모.
주의: 이 앱의 데이터와 모델은 합성 데이터 기준이며, 실측 결과가 아닙니다.
절감액은 한전 요금표 산식 기반 추정치이며, 실제 절감액을 보장하지 않습니다.

실행:
    ../venv/bin/streamlit run app.py --server.headless true
    → http://localhost:8501

언어: 상단 선택기로 한국어/English 전환 가능 (기본값 한국어).
기능(모델, 절감 산식, 합성 데이터 배너)은 언어와 무관하게 동일합니다.
"""

from datetime import timedelta
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

BASE = Path(__file__).parent  # deploy 폴더: 모델·데이터가 같은 폴더 안에 있음
MODEL_PATH = BASE / "model.pkl"
SAMPLE_PATH = BASE / "data" / "synthetic_load_15min.csv"

# 요금표 단가 (2026.4.16 기준, 한전 전기요금표 — invention-brief-peakguard.md 참조)
# (한국어 라벨, 영어 라벨, 단가) — 단가는 언어와 무관하게 동일
TARIFF_OPTIONS = [
    ("산업용(을) 고압A 선택Ⅱ — 8,320원/kW·월",
     "Industrial (B) high-voltage A, option II — KRW 8,320/kW·month", 8320),
    ("산업용(갑)Ⅰ 고압A 선택Ⅱ — 7,470원/kW·월",
     "Industrial (A) I high-voltage A, option II — KRW 7,470/kW·month", 7470),
]

BUCKET_LABELS = {
    "morning(08-12)": ("오전 08–12시", "Morning 08–12"),
    "midday(12-15)": ("정오 12–15시", "Midday 12–15"),
    "afternoon(15-18)": ("오후 15–18시", "Afternoon 15–18"),
    "other": ("그 외 시간대", "Other hours"),
}

STR = {
    "page_title": ("PeakGuard — 내일 피크 예측 데모", "PeakGuard — Tomorrow's Peak Forecast Demo"),
    "title": ("PeakGuard — 내일 피크 예측 데모", "PeakGuard — Tomorrow's Peak Forecast Demo"),
    "warning": (
        "⚠️ 데모 데이터는 합성 데이터이며 실측 결과가 아닙니다. "
        "이 앱의 예측 피크와 절감액은 실제 공장 측정값이 아니며, "
        "절감액은 요금표 산식 기반 추정치입니다.",
        "⚠️ Demo data is synthetic, not measured results. "
        "Predicted peaks and savings in this app are not real factory measurements; "
        "savings are tariff-formula estimates.",
    ),
    "model_caption": (
        "모델: 다음 날 일간 최대 15분 피크(kW) 회귀 + 피크 시간대 4구간 분류 | "
        "학습 데이터 종류: {kind} | "
        "합성 검증 지표: MAPE {mape:.2f}%"
        "(MAE {mae:.2f} kW, 시간대 정확도 {acc:.1%})",
        "Model: next-day daily max 15-min peak (kW) regression + 4-bucket peak-window classification | "
        "Training data: {kind} | "
        "Synthetic validation: MAPE {mape:.2f}%"
        " (MAE {mae:.2f} kW, window accuracy {acc:.1%})",
    ),
    "h1": ("1. 예측 조건 입력", "1. Forecast inputs"),
    "target_date": ("예측 대상 날짜 (다음 날)", "Target date (next day)"),
    "load_sample": ("합성 샘플 이력 불러오기", "Load synthetic sample history"),
    "recent7": ("최근 7일 일간 피크 (kW) — 오래된 날부터 순서대로",
               "Daily peaks, last 7 days (kW) — oldest first"),
    "days_ago": ("{n}일 전", "{n} days ago"),
    "yesterday": ("전일", "Yesterday"),
    "energy_lag1": ("전일 전력량 (kWh)", "Yesterday's energy (kWh)"),
    "peak_hour_lag1": ("전일 피크 시각 (시, 예: 14.5 = 14시 30분)",
                       "Yesterday's peak hour (e.g., 14.5 = 14:30)"),
    "h2": ("2. 예측 결과", "2. Forecast result"),
    "pred_peak": ("예측 피크 (다음 날 최대 15분)", "Predicted peak (next-day max 15-min)"),
    "pred_window": ("예측 피크 시간대", "Predicted peak window"),
    "prev_peak": ("전일 피크 (참고)", "Yesterday's peak (reference)"),
    "h3": ("3. 최근 7일 부하 곡선 (합성 샘플)", "3. Last 7 days load curve (synthetic sample)"),
    "chart_caption": ("15분 단위 부하(kW) — 합성 샘플 기준", "15-min load (kW) — synthetic sample"),
    "bar_col": ("일간 피크(kW)", "Daily peak (kW)"),
    "bar_forecast": ("예측(다음 날)", "Forecast (next day)"),
    "h4": ("4. 기본요금 절감 시뮬레이션 (요금표 산식 기반 추정치)",
           "4. Basic-charge savings simulation (tariff-formula estimate)"),
    "formula_caption": (
        "산식: 연간 절감액 = 기준 피크(kW) × 절감률 × 기본요금 단가(원/kW·월) × 12개월. "
        "절감된 피크가 12개월 요금적용전력으로 유지된다고 가정한 추정치이며, "
        "실제 절감액은 요금적용전력 산정 규칙(직전 12개월 특정 월 최대값)과 실제 부하에 따라 달라집니다.",
        "Formula: annual saving = base peak (kW) × reduction × basic-charge rate (KRW/kW·month) × 12 months. "
        "Assumes the shaved peak stays as the billed demand for 12 months; "
        "actual savings depend on the billed-demand rule (max of the trailing 12 months) and real load.",
    ),
    "base_peak": ("기준 피크 (kW)", "Base peak (kW)"),
    "reduction": ("피크 절감률 (%)", "Peak reduction (%)"),
    "tariff": ("기본요금 단가", "Basic-charge rate"),
    "peak_shaved": ("절감 피크", "Peak shaved"),
    "monthly_save": ("월 절감 추정치", "Monthly saving (est.)"),
    "annual_save": ("연 절감 추정치", "Annual saving (est.)"),
    "expander": ("모델 정보 및 한계", "Model info and limits"),
    "expander_body": (
        "- 학습 데이터: 합성 공장 15분 부하 데이터(계약전력 500kW급, 1년) — 실측이 아닙니다.\n"
        "- 합성 검증 지표: 피크 MAE {mae:.2f} kW, "
        "MAPE {mape:.2f}%, "
        "피크 시간대 정확도 {acc:.1%} "
        "(시간대 정확도는 개입 알림 용도로 부족합니다).\n"
        "- 실제 공장 데이터(CSV: timestamp, kw, 최소 30일)로 재학습하면 실측 기준으로 전환됩니다.\n"
        "- 절감액은 요금표 산식 추정치이며, 실측 절감 증명은 유료 고객 확보 이후 단계입니다.",
        "- Training data: synthetic factory 15-min load data (500 kW class, 1 year) — not measured.\n"
        "- Synthetic validation: peak MAE {mae:.2f} kW, "
        "MAPE {mape:.2f}%, "
        "peak-window accuracy {acc:.1%} "
        "(window accuracy is insufficient for intervention alerts).\n"
        "- Retraining on real factory data (CSV: timestamp, kw, min 30 days) switches to measured basis.\n"
        "- Savings are tariff-formula estimates; measured proof of savings comes after a paying customer.",
    ),
}


@st.cache_resource
def load_model():
    bundle = joblib.load(MODEL_PATH)
    return bundle


@st.cache_data
def load_sample():
    df = pd.read_csv(SAMPLE_PATH, comment="#", parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def daily_stats(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["date"] = d["timestamp"].dt.normalize()
    peak_rows = d.loc[d.groupby("date")["kw"].idxmax()].set_index("date")
    daily = pd.DataFrame({
        "peak_kw": d.groupby("date")["kw"].max(),
        "peak_hour": peak_rows["timestamp"].dt.hour
        + peak_rows["timestamp"].dt.minute / 60.0,
        "energy_kwh": d.groupby("date")["kw"].sum() * 0.25,
    })
    return daily


st.set_page_config(page_title="PeakGuard — 내일 피크 예측 데모", layout="wide")

# ---------- 언어 전환 (기본값 한국어, 기능 동일) ----------
_lang_choice = st.selectbox("언어 / Language", ["한국어", "English"], index=0)
LANG = 0 if _lang_choice == "한국어" else 1


def t(key: str) -> str:
    return STR[key][LANG]


st.title(t("title"))
st.warning(t("warning"))

bundle = load_model()
sample = load_sample()
daily = daily_stats(sample)
last_date = daily.index[-1].date()
last7 = daily.iloc[-7:]

st.caption(
    t("model_caption").format(
        kind=bundle["data_kind"],
        mape=bundle["metrics"]["peak_mape_pct"],
        mae=bundle["metrics"]["peak_mae_kw"],
        acc=bundle["metrics"]["bucket_accuracy"],
    )
)

# ---------- 입력: 예측 날짜 + 최근 피크 이력 ----------
st.header(t("h1"))
col_a, col_b = st.columns(2)
with col_a:
    target_date = st.date_input(
        t("target_date"),
        value=last_date + timedelta(days=1),
    )
with col_b:
    if st.button(t("load_sample")):
        for i, v in enumerate(last7["peak_kw"]):
            st.session_state[f"peak_{i}"] = round(float(v), 1)
        st.session_state["energy_in"] = round(float(last7["energy_kwh"].iloc[-1]), 1)
        st.session_state["peak_hour_in"] = round(float(last7["peak_hour"].iloc[-1]), 2)

for i, v in enumerate(last7["peak_kw"]):
    st.session_state.setdefault(f"peak_{i}", round(float(v), 1))
st.session_state.setdefault("energy_in", round(float(last7["energy_kwh"].iloc[-1]), 1))
st.session_state.setdefault("peak_hour_in", round(float(last7["peak_hour"].iloc[-1]), 2))

st.subheader(t("recent7"))
peak_cols = st.columns(7)
peaks = []
for i, c in enumerate(peak_cols):
    with c:
        peaks.append(st.number_input(
            t("days_ago").format(n=i - 7) if i < 6 else t("yesterday"),
            value=float(st.session_state[f"peak_{i}"]),
            min_value=0.0, step=1.0, key=f"peak_{i}",
        ))
col_e, col_h = st.columns(2)
with col_e:
    energy_lag1 = st.number_input(
        t("energy_lag1"), value=float(st.session_state["energy_in"]),
        min_value=0.0, step=10.0, key="energy_in",
    )
with col_h:
    peak_hour_lag1 = st.number_input(
        t("peak_hour_lag1"),
        value=float(st.session_state["peak_hour_in"]),
        min_value=0.0, max_value=23.75, step=0.25, key="peak_hour_in",
    )

# ---------- 예측 ----------
# peaks[0] = 7일 전 ... peaks[6] = 전일(lag1)
features = {
    "dow": target_date.weekday(),
    "month": target_date.month,
    "is_weekend": 1 if target_date.weekday() >= 5 else 0,
    "peak_lag1": peaks[6],
    "peak_lag2": peaks[5],
    "peak_lag3": peaks[4],
    "peak_lag7": peaks[0],
    "peak_mean3": sum(peaks[4:7]) / 3,
    "peak_mean7": sum(peaks) / 7,
    "peak_max7": max(peaks),
    "energy_lag1": energy_lag1,
    "peak_hour_lag1": peak_hour_lag1,
}
X = pd.DataFrame([features], columns=bundle["feature_names"])
pred_kw = float(bundle["peak_model"].predict(X)[0])
pred_bucket = bundle["metrics"]["bucket_labels"][int(bundle["bucket_model"].predict(X)[0])]

st.header(t("h2"))
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(t("pred_peak"), f"{pred_kw:,.1f} kW")
with m2:
    st.metric(t("pred_window"), BUCKET_LABELS[pred_bucket][LANG])
with m3:
    st.metric(t("prev_peak"), f"{peaks[6]:,.1f} kW")

# ---------- 차트: 최근 7일 부하 곡선 + 일간 피크 ----------
st.header(t("h3"))
chart_df = sample[sample["timestamp"].dt.normalize() >= last7.index[0]].copy()
st.line_chart(chart_df.set_index("timestamp")["kw"], height=300)
st.caption(t("chart_caption"))

bar_data = pd.DataFrame({
    t("bar_col"): list(last7["peak_kw"]) + [pred_kw],
}, index=[d.strftime("%m-%d") for d in last7.index] + [t("bar_forecast")])
st.bar_chart(bar_data, height=250)

# ---------- 절감 시뮬레이션 ----------
st.header(t("h4"))
st.caption(t("formula_caption"))
s1, s2, s3 = st.columns(3)
with s1:
    base_peak = st.number_input(
        t("base_peak"), value=round(pred_kw, 1), min_value=0.0, step=1.0,
    )
with s2:
    reduction = st.slider(t("reduction"), 1, 30, 10) / 100.0
with s3:
    tariff_label = st.selectbox(
        t("tariff"), [opt[LANG] for opt in TARIFF_OPTIONS])
rate = next(opt[2] for opt in TARIFF_OPTIONS if opt[LANG] == tariff_label)
monthly_save = base_peak * reduction * rate
annual_save = monthly_save * 12
c1, c2, c3 = st.columns(3)
with c1:
    st.metric(t("peak_shaved"), f"{base_peak * reduction:,.1f} kW")
with c2:
    if LANG == 0:
        st.metric(t("monthly_save"), f"{monthly_save:,.0f} 원")
    else:
        st.metric(t("monthly_save"), f"KRW {monthly_save:,.0f}")
with c3:
    if LANG == 0:
        st.metric(t("annual_save"), f"{annual_save:,.0f} 원")
    else:
        st.metric(t("annual_save"), f"KRW {annual_save:,.0f}")

with st.expander(t("expander")):
    st.write(
        t("expander_body").format(
            mae=bundle["metrics"]["peak_mae_kw"],
            mape=bundle["metrics"]["peak_mape_pct"],
            acc=bundle["metrics"]["bucket_accuracy"],
        )
    )
