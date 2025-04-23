import streamlit as st
import random
from PIL import Image
import os
import ollama
import time

# --- 설정값 ---
DRIVER_KEYWORDS = {
    1: ["반려동물", "게임", "SNS"],
    2: ["마피아", "액션 영화", "뱀파이어 이야기"],
    3: ["좋은 식당", "농사", "여행"],
    4: ["종교", "팬데믹", "전쟁"]
}

DRIVER_PERSONALITY = {
    1: {
        "interested": "음~ 이거 좀 흥미로운데요? 계속 얘기해보시죠. [+{delta}원]",
        "bored": "에이, 그런 얘긴 질렸어요. 다음 얘기나 해보죠. [+{delta}원]",
        "image": "images/driver1.jpeg"
    },
    2: {
        "interested": "하하! 이런 얘기가 내 취향이지. 더 자세히 말해봐요. [+{delta}원]",
        "bored": "흥. 별 볼일 없군요. 이런 건 재미없어요. [+{delta}원]",
        "image": "images/driver2.jpeg"
    },
    3: {
        "interested": "오~ 이런 현실적인 이야기는 좋지. 계속해요. [+{delta}원]",
        "bored": "그게 다인가요? 현실감이 없네요. [+{delta}원]",
        "image": "images/driver3.jpeg"
    },
    4: {
        "interested": "...그 이야기는 익숙하군요. 계속 들려주세요. [+{delta}원]",
        "bored": "무의미한 소리입니다. 당신은 아무것도 모르고 있군요. [+{delta}원]",
        "image": "images/driver4.jpeg"
    }
}

# --- LLM 응답 처리 ---
def ask_llm(driver_num, story):
    keywords = DRIVER_KEYWORDS[driver_num]
    personality = DRIVER_PERSONALITY[driver_num]
    prompt = f"""기사 번호: {driver_num}
선호 키워드: {', '.join(keywords)}
성격: {personality['interested']} / {personality['bored']}
이야기: "{story}"
이 이야기에 대해 기사가 어떤 반응을 보일지 말해줘.
- 기사 성격에 맞게 말해줘
- 이야기의 흥미 여부(키워드 매칭 외에도 내용이 기사 취향인지 고려)
- 흥미롭다면 미터기 +3~7, 지루하면 +10~20 중에서 하나 고르고, 이유도 말해
- 최대한 자신이 몇번 기사인지는 말하면 안돼 
포맷:
반응: (말풍선)
흥미도: (high/low)
요금증가: (정수)"""
    response = ollama.chat(model='eeve-korean-10.8b', messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

def generate_next_story(driver_num):
    prompt = f'''
택시 기사 {driver_num}번이 흥미로워할 만한 짧은 이야기 1개를 만들어주세요.

[요구사항]
- 제목 1개와, 제목과 관련된 3줄 이내의 짧은 이야기 1개로 구성
- 반드시 아래 형식만 지켜서 출력하세요. 불필요한 설명은 하지 마세요.

[형식]
제목: (제목)
이야기: (3줄 이내 이야기)

[기사 키워드]
{', '.join(DRIVER_KEYWORDS[driver_num])}
'''
    response = ollama.chat(model='eeve-korean-10.8b', messages=[{"role": "user", "content": prompt}])
    result = response['message']['content'].strip()
    # 제목과 이야기만 추출해서 반환
    if "제목:" in result and "이야기:" in result:
        try:
            title = result.split("제목:")[1].split("\n")[0].strip()
            story = result.split("이야기:")[1].strip()
            return f"제목: {title}\n이야기: {story}"
        except Exception:
            return result
    return result

# --- 상태 초기화 ---
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.driver_num = random.randint(1, 4)
    st.session_state.meter = 0
    st.session_state.round = 0
    st.session_state.history = []
    st.session_state.current_story_options = []
    st.session_state.story_selected = False
    st.session_state.pending_reaction = ""

# --- 페이지 설정 ---
st.set_page_config(page_title="지옥할증택시", layout="centered")
page = st.sidebar.radio("페이지 이동", ["🚗게임 방법 보기", "💀게임 시작하기"])

if page == "🚗게임 방법 보기":
    st.title("📖 게임 방법")
    st.markdown("""
**🕯 지옥할증택시 괴담**
심야에 호출한 의문의 택시에 탑승한 당신...
이 택시에서 살아서 내리기 위해서는 **기사의 흥미를 끄는 이야기를 들려줘야 합니다.**

- 각 기사마다 좋아하는 키워드가 다릅니다:
    - 1번 기사:  반려동물, 게임, SNS
    - 2번 기사: 마피아, 액션 영화, 뱀파이어 이야기
    - 3번 기사: 좋은 식당, 농사, 여행
    - 4번 기사: 종교적, 팬데믹, 전쟁
- 기사의 흥미가 떨어지면 **요금(저주)**이 더 빨리 오릅니다.
- 이야기가 끝날 때마다 **기사가 다음 이야기를 유도**합니다.
- 요금이 곧 **저주의 강도**입니다...
🚖 당신이 탄 택시는... 정체를 알 수 없는 기사입니다.
이야기를 들려주며 단서를 모아보세요.
    """, unsafe_allow_html=True)

elif page == "💀게임 시작하기":
    st.title("🚖 지옥할증택시 괴담")
    img_path = "images/taxi_night.png"
    if os.path.exists(img_path):
        st.image(img_path, caption="심야의 수상한 택시", use_column_width=True)

    if st.session_state.round == 0:
        st.subheader("🛫 프롤로그")
        st.markdown("기사: 오늘 하루는 어땠습니까?")
        if st.button("그냥 출근했죠 뭐"):
            st.session_state.meter += 20
            st.session_state.round = 1
            st.success("미터기의 숫자가 치솟는다. +20 ")
            st.success("나: ...뭔가 이상하다. 위기를 느꼈다.")
            st.info("기사의 흥미를 끌어 최대한 낮은 요금으로 살아남자!")

    if 1 <= st.session_state.round <= 5:
        # 이야기 선택지 생성
        if not st.session_state.story_selected and not st.session_state.current_story_options:
            current_driver = st.session_state.driver_num
            other_drivers = [d for d in [1, 2, 3, 4] if d != current_driver]
            selected_drivers = random.sample(other_drivers, 2) + [current_driver]
            random.shuffle(selected_drivers)
            st.session_state.current_story_options = []
            for driver in selected_drivers:
                story = generate_next_story(driver)
                st.session_state.current_story_options.append({
                    "story": story,
                    "driver": driver
                })

        # 이야기 선택 UI
        if not st.session_state.story_selected:
            story_texts = [opt["story"] for opt in st.session_state.current_story_options]
            story = st.radio("🧠 어떤 이야기를 꺼내볼까?", story_texts, key=f"story_{st.session_state.round}")
            if st.button("이야기 선택하기"):
                st.session_state.selected_story = story
                st.session_state.story_selected = True

        # 이야기 선택 후: 기사 반응 + 다음 이야기 버튼 등장
        if st.session_state.story_selected:
            # 선택한 이야기의 기사 번호 찾기
            selected_story = st.session_state.selected_story
            selected_idx = [opt["story"] for opt in st.session_state.current_story_options].index(selected_story)
            selected_driver = st.session_state.current_story_options[selected_idx]["driver"]
            current_driver = st.session_state.driver_num

            # 기사 번호가 같으면 흥미, 다르면 지루함
            if selected_driver == current_driver:
                delta = random.randint(3, 7)
                reaction = DRIVER_PERSONALITY[current_driver]["interested"].format(delta=delta)
            else:
                delta = random.randint(10, 20)
                reaction = DRIVER_PERSONALITY[current_driver]["bored"].format(delta=delta)

            st.session_state.meter += delta
            st.markdown("#### 나는 이야기를 시작했다...")
            time.sleep(5)
            personality = DRIVER_PERSONALITY[current_driver]
            if os.path.exists(personality["image"]):
                st.image(personality["image"], width=300)
            st.write(f"**기사 반응**: {reaction}")
            if delta >= 15:
                meter_desc = "미터기가 급격히 치솟았다..."
            elif delta >= 10:
                meter_desc = "미터기가 빠르게 움직였다."
            else:
                meter_desc = "미터기가 천천히 올라갔다."
            st.write(f"**{meter_desc}**")
            st.progress(min(st.session_state.meter, 100))

            # ⏭ 다음 이야기 버튼
            if st.button("다음 이야기"):
                st.session_state.round += 1
                st.session_state.story_selected = False
                st.session_state.current_story_options = []
                st.markdown("##### 다음 이야기를 시작하자")

    if st.session_state.round > 3:
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
                double_fare = total_fare * 2
                st.error(f"오답입니다. 정체는 {true_driver}번 기사였으며, 당신은 {double_fare}원의 저주를 받았습니다.")
            st.info("🚨 저주의 상세 내용은 직접 경험해 보기전엔 알 수 없습니다…")
            if st.button("다시 시작하기"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.experimental_rerun()
