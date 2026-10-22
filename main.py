
# main.py
# 어제의 박스오피스
# 초보자도 이해하기 쉽도록 한국어 주석을 달았습니다.

import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# --------------------------------------------------
# 1. 기본 화면 설정
# --------------------------------------------------
st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")
st.caption("영화진흥위원회(KOBIS) 일별 박스오피스 데이터")


# --------------------------------------------------
# 2. 한국 시간 기준으로 어제 날짜 계산
# --------------------------------------------------
# 서버가 해외 시간대를 사용하더라도 한국 시간으로 계산합니다.
한국시간 = ZoneInfo("Asia/Seoul")
오늘 = datetime.now(한국시간).date()
어제 = 오늘 - timedelta(days=1)

# API에서 요구하는 날짜 형식: YYYYMMDD
조회날짜 = 어제.strftime("%Y%m%d")
표시날짜 = 어제.strftime("%Y년 %m월 %d일")


# --------------------------------------------------
# 3. API 주소 및 인증키 준비
# --------------------------------------------------
API주소 = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

st.write(f"📅 **조회 날짜: {표시날짜}**")

# 인증키는 코드에 직접 입력하지 않고 Streamlit 비밀 금고에서 읽습니다.
try:
    인증키 = st.secrets["KOBIS_KEY"]
except Exception:
    st.error(
        "🔑 KOBIS 인증키를 찾을 수 없습니다.\n\n"
        "확인할 사항:\n"
        "1. Streamlit Cloud에서 앱의 Settings → Secrets를 엽니다.\n"
        "2. KOBIS_KEY라는 이름으로 발급받은 인증키를 등록합니다.\n"
        "3. 저장한 뒤 앱을 다시 실행합니다."
    )
    st.stop()


# --------------------------------------------------
# 4. KOBIS API 요청 및 데이터 확인
# --------------------------------------------------
요청변수 = {
    "key": 인증키,
    "targetDt": 조회날짜
}

try:
    응답 = requests.get(
        API주소,
        params=요청변수,
        timeout=20
    )

    # 인터넷 연결 또는 서버 측 HTTP 오류 확인
    응답.raise_for_status()

    # JSON 응답으로 변환
    결과 = 응답.json()

except requests.exceptions.Timeout:
    st.error(
        "⏰ KOBIS 서버 응답 시간이 초과되었습니다.\n\n"
        "잠시 기다렸다가 새로고침해 주세요."
    )
    st.stop()

except requests.exceptions.HTTPError as 오류:
    st.error(
        f"🌐 API 요청에 실패했습니다. (HTTP 오류: {오류})\n\n"
        "인터넷 연결, KOBIS 서버 상태를 확인한 뒤 다시 시도해 주세요."
    )
    st.stop()

except requests.exceptions.RequestException as 오류:
    st.error(
        f"🌐 KOBIS 서버에 연결할 수 없습니다.\n\n"
        f"오류 내용: {오류}\n\n"
        "네트워크 연결과 KOBIS 서버 상태를 확인해 주세요."
    )
    st.stop()

except ValueError:
    st.error(
        "📄 서버 응답을 JSON 데이터로 읽지 못했습니다.\n\n"
        "KOBIS 서버 상태를 확인한 뒤 다시 시도해 주세요."
    )
    st.stop()


# --------------------------------------------------
# 5. API 오류 상자(faultInfo) 확인
# --------------------------------------------------
# 인증키가 잘못되어도 HTTP 상태코드는 200일 수 있으므로
# 반드시 응답 안의 faultInfo도 확인합니다.
if not isinstance(결과, dict):
    st.error("서버 응답 형식이 예상과 다릅니다. 잠시 후 다시 시도해 주세요.")
    st.stop()

if "faultInfo" in 결과:
    오류정보 = 결과["faultInfo"]

    오류메시지 = (
        오류정보.get("message")
        or 오류정보.get("errorMessage")
        or "상세 오류 메시지가 제공되지 않았습니다."
    )

    오류코드 = (
        오류정보.get("errorCode")
        or 오류정보.get("error_code")
        or "확인되지 않음"
    )

    st.error(
        "🚨 KOBIS API에서 오류를 반환했습니다.\n\n"
        f"- 오류 코드: {오류코드}\n"
        f"- 오류 내용: {오류메시지}\n\n"
        "확인할 사항:\n"
        "1. KOBIS_KEY가 정확한지 확인합니다.\n"
        "2. 인증키가 정상적으로 발급되었는지 확인합니다.\n"
        "3. KOBIS API 이용 안내 및 서버 상태를 확인합니다."
    )
    st.stop()


# --------------------------------------------------
# 6. 영화 목록 가져오기
# --------------------------------------------------
박스오피스결과 = 결과.get("boxOfficeResult")

if not isinstance(박스오피스결과, dict):
    st.error(
        "📄 박스오피스 결과를 찾을 수 없습니다.\n\n"
        "API 응답 구조가 변경되었거나 서버에서 예상하지 못한 "
        "응답을 보냈을 수 있습니다. 잠시 후 다시 시도해 주세요."
    )
    st.stop()

영화목록 = 박스오피스결과.get("dailyBoxOfficeList", [])

if not isinstance(영화목록, list) or len(영화목록) == 0:
    st.warning(
        "🎞️ 조회된 영화 목록이 없습니다.\n\n"
        "확인할 사항:\n"
        "1. 어제 날짜의 박스오피스 자료가 등록되었는지 확인합니다.\n"
        "2. KOBIS 홈페이지에서 해당 날짜의 자료를 확인합니다.\n"
        "3. 자료가 아직 집계되지 않았다면 나중에 다시 실행해 주세요."
    )
    st.stop()


# --------------------------------------------------
# 7. 표와 그래프에 사용할 데이터 정리
# --------------------------------------------------
데이터 = pd.DataFrame(영화목록)

# API에서 숫자도 문자열로 제공하므로 숫자형으로 변환합니다.
숫자열 = [
    "rank",
    "audiCnt",
    "audiAcc",
    "scrnCnt",
    "showCnt",
    "rankInten"
]

for 열 in 숫자열:
    if 열 in 데이터.columns:
        데이터[열] = pd.to_numeric(
            데이터[열],
            errors="coerce"
        ).fillna(0)

# 화면에 표시할 한국어 열 이름으로 바꿉니다.
필요한열 = {
    "rank": "순위",
    "movieNm": "영화명",
    "openDt": "개봉일",
    "audiCnt": "관객수",
    "audiAcc": "누적관객",
    "scrnCnt": "스크린수"
}

# 혹시 API 응답에서 일부 필드가 빠졌을 경우에도 앱이 멈추지 않도록 합니다.
for 원래이름 in 필요한열:
    if 원래이름 not in 데이터.columns:
        데이터[원래이름] = ""

표데이터 = 데이터[list(필요한열.keys())].rename(
    columns=필요한열
)

표데이터["순위"] = pd.to_numeric(
    표데이터["순위"], errors="coerce"
).fillna(0).astype(int)

for 열 in ["관객수", "누적관객", "스크린수"]:
    표데이터[열] = pd.to_numeric(
        표데이터[열], errors="coerce"
    ).fillna(0).astype(int)

# 순위가 낮은 숫자부터 정렬합니다.
표데이터 = 표데이터.sort_values("순위").reset_index(drop=True)

# 첫 번째 영화가 1위 영화입니다.
일위영화 = 표데이터.iloc[0]


# --------------------------------------------------
# 8. 1위 영화 소개
# --------------------------------------------------
st.divider()
st.subheader("🏆 오늘의 박스오피스 1위")
st.markdown(f"### 🎬 {일위영화['영화명']}")

# 세 개의 지표 카드를 나란히 표시합니다.
카드1, 카드2, 카드3 = st.columns(3)

카드1.metric(
    label="당일 관객수",
    value=f"{일위영화['관객수']:,}명"
)

카드2.metric(
    label="누적 관객수",
    value=f"{일위영화['누적관객']:,}명"
)

카드3.metric(
    label="스크린수",
    value=f"{일위영화['스크린수']:,}개"
)


# --------------------------------------------------
# 9. 관객수 상위 5편 막대그래프
# --------------------------------------------------
st.divider()
st.subheader("📊 관객수 상위 5편")

상위5편 = 표데이터.sort_values(
    "관객수", ascending=False
).head(5).copy()

if not 상위5편.empty:
    # 영화 이름이 긴 경우에도 읽기 쉽도록 가로 막대그래프를 사용합니다.
    그래프 = px.bar(
        상위5편.sort_values("관객수", ascending=True),
        x="관객수",
        y="영화명",
        orientation="h",
        text="관객수",
        labels={
            "관객수": "당일 관객수(명)",
            "영화명": "영화"
        },
        title=f"{표시날짜} 관객수 상위 5편"
    )

    그래프.update_traces(
        texttemplate="%{text:,.0f}명",
        textposition="outside",
        cliponaxis=False
    )

    그래프.update_layout(
        xaxis=dict(
            tickformat=",",
            rangemode="tozero"
        ),
        yaxis_title="",
        margin=dict(l=10, r=70, t=60, b=20)
    )

    st.plotly_chart(그래프, use_container_width=True)


# --------------------------------------------------
# 10. 전체 박스오피스 표
# --------------------------------------------------
st.divider()
st.subheader("📋 전체 박스오피스 순위")

# 관객수와 누적 관객수는 천 단위 쉼표로 표시합니다.
st.dataframe(
    표데이터.style.format({
        "관객수": "{:,}명",
        "누적관객": "{:,}명",
        "스크린수": "{:,}개"
    }),
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 11. 데이터 출처
# --------------------------------------------------
st.caption(
    "데이터 출처: 영화진흥위원회(KOBIS) 일별 박스오피스 API"
)
st.caption(
    "※ 관객수는 해당 날짜의 집계값이며, "
    "자료 반영 시점에 따라 값이 달라질 수 있습니다."
)
