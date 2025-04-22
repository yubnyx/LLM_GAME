# app.py
import streamlit as st
import random
import time
from PIL import Image
import os
import ollama

# --- 설정값 ---
DRIVER_KEYWORDS = {
    1: ["올림픽", "선거", "반려동물", "게임", "SNS"],
    2: ["마피아", "액션 영화", "흡혈귀 전설", "총기"],
    3: ["좋은 식당", "농사", "경제불황", "빈민가 여행", "명품"],
    4: ["내세", "종교적 체험", "팬데믹", "전쟁"]
}

DRIVER_PERSONALITY = {
    1: {
        "interested": "음~ 이거 좀 흥미로운데요? 계속 얘기해보시죠. [+{delta}원]",
        "bored": "에이, 그런 얘긴 질렸어요. 다음 얘기나 해보죠. [+{delta}원]",
        "image": "images/driver1.png"
    },
    2: {
        "interested": "하하! 이런 얘기가 내 취향이지. 더 자세히 말해봐요. [+{delta}원]",
        "bored": "흥. 별 볼일 없군요. 이런 건 재미없어요. [+{delta}원]",
        "image": "images/driver2.png"
    },
    3: {
        "interested": "오~ 이런 현실적인 이야기는 좋지. 계속해요. [+{delta}원]",
        "bored": "그게 다인가요? 현실감이 없네요. [+{delta}원]",
        "image": "images/driver3.png"
    },
    4: {
        "interested": "...그 이야기는 익숙하군요. 계속 들려주세요. [+{delta}원]",
        "bored": "무의미한 소리입니다. 당신은 아무것도 모르고 있군요. [+{delta}원]",
        "image": "images/driver4.png"
    }
}

# --- LLM 응답 처리 ---
def ask_llm(driver_num, story):
    keywords = DRIVER_KEYWORDS[driver_num]
    personality = DRIVER_PERSONALITY[driver_num]

    prompt = f"""
    기사 번호: {driver_num}
    선호 키워드: {', '.join(keywords)}
    성격: {personality['interested']} / {personality['bored']}

    이야기: "{story}"

    이 이야기에 대해 기사가 어떤 반응을 보일지 말해줘.
    - 기사 성격에 맞게 말해
    - 이야기의 흥미 여부(키워드 매칭 외에도 내용이 기사 취향인지 고려)
    - 흥미롭다면 미터기 +3~7, 지루하면 +10~20 중에서 하나 고르고, 이유도 말해
    포맷:
    반응: (말풍선)
    흥미도: (high/low)
    요금증가: (정수)
    """

    response = ollama.chat(
        model='eeve',
        messages=[{"role": "user", "content": prompt}]
    )

    return response['message']['content']

# 다음 이야기 생성 (선택적 확장)
def generate_next_story(current_story, driver_num):
    prompt = f'''
    지금까지의 이야기: "{current_story}"
    택시 기사는 {driver_num}번 기사입니다.
    기사 성격과 키워드에 어울리는 다음 이야기를 하나 만들어주세요.
    짧은 괴담 형식으로, 흥미로운 전개가 되게 해주세요.
    ''')
    response = ollama.chat(
        model='eeve',
        messages=[{"role": "user", "content": prompt}]
    )
    return response['message']['content'].strip()

# --- 초기 스토리 ---
story_steps = {
    1: [
        "SNS 실시간 방송 중 실종된 인플루언서",
        "전쟁터에서 돌아온 군인의 또 다른 그림자",
        "빈민가 맛집의 단골 손님은 누구였나"
    ],
    2: [
        "반려견이 찍은 사진 속 사람은 누구인가",
        "수혈 받은 뒤 달라진 성격",
        "수입 명품 백에 들어 있던 건…"
    ],
    3: [
        "게임 속 버그가 현실로 나타난다면?",
        "전염병이 멈춘 마을에서 다시 돌아온 아이",
        "총기 밀매범의 일기장에서 발견된 낙서"
    ],
    4: [
        "어린 시절 장난감에 담긴 진실",
        "끝없는 터널을 도는 택시 기사",
        "매일 반복되는 같은 악몽, 그리고 깨어나지 않는 아침"
    ]
}

# --- 상태 관리 ---
if "driver_num" not in st.session_state:
    st.session_state.driver_num = random.randint(1, 4)
    st.session_state.meter = 0
    st.session_state.round = 1
    st.session_state.history = []

st.set_page_config(page_title="지옥할증택시", layout="centered")
st.title("🚖 지옥할증택시 괴담")
img_path = "images/taxi_night.png"
if os.path.exists(img_path):
    st.image(img_path, caption="심야의 수상한 택시", use_column_width=True)
st.write("심야에 호출한 수상한 택시… 살아서 내릴 수 있을까?")

# --- 이야기 선택 ---
if st.session_state.round <= len(story_steps):
    current_stories = story_steps[st.session_state.round]
    story = st.radio("👻 기사에게 들려줄 괴담을 선택하세요", current_stories)

    if st.button("이야기 들려주기"):
        st.session_state.history.append(story)

        driver = st.session_state.driver_num
        personality = DRIVER_PERSONALITY[driver]

        # LLM 호출
        llm_result = ask_llm(driver, story)
        lines = llm_result.strip().split("\n")
        reaction = lines[0].replace("반응:", "").strip()
        delta = int(lines[2].split(":")[1].strip())
        st.session_state.meter += delta

        # 기사 이미지 출력
        if os.path.exists(personality["image"]):
            st.image(personality["image"], caption=f"{driver}번 기사", width=300)

        # 반응 출력
        st.write(f"**기사 반응**: {reaction} [+{delta}원]")

        st.progress(min(st.session_state.meter, 100))
        st.session_state.round += 1

# --- 최종 추리 ---
if st.session_state.round > len(story_steps):
    st.write("---")
    st.subheader("🧠 기사 정체 추리")
    guess = st.selectbox("이 택시기사는 몇 번 기사일까요?", [1, 2, 3, 4])
    if st.button("정체 공개!"):
        true_driver = st.session_state.driver_num
        total_fare = st.session_state.meter * 100
        if os.path.exists(DRIVER_PERSONALITY[true_driver]["image"]):
            st.image(DRIVER_PERSONALITY[true_driver]["image"], caption=f"정답: {true_driver}번 기사", width=300)
        if guess == true_driver:
            st.success(f"정답입니다! 당신은 겨우겨우 {total_fare}원의 저주만 받았습니다…")
        else:
            st.error(f"오답입니다. 정체는 {true_driver}번 기사였으며, 당신은 {total_fare}원의 저주를 받았습니다.")
        st.info("🚨 저주의 상세 내용은 다시는 같은 이야기를 반복하게 되는 삶입니다…")
        if st.button("다시 시작하기"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()
