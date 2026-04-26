import streamlit as st
import json
import time
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent

# ──────────────────────────────────────────
# 사이드바 (점수 + 문제별 정오표)
# ──────────────────────────────────────────
def render_sidebar(quiz_data):
    total = len(quiz_data)
    total_points = sum(int(q.get("points", 1)) for q in quiz_data)
    with st.sidebar:
        st.markdown(f"### 점수: **{st.session_state.score} / {total_points}**")
        rows = []
        for i in range(total):
            v = st.session_state.per_question.get(i)
            if v is True:
                status = "✅ 정답"
            elif v is False:
                status = "❌ 오답"
            else:
                status = "—"
            rows.append({"문제": i + 1, "결과": status})
        st.dataframe(rows, hide_index=True, use_container_width=True)

# ──────────────────────────────────────────
# 캐싱: 퀴즈 데이터 로드 
# ──────────────────────────────────────────
@st.cache_data
def load_quiz_data():
    with open(APP_DIR / "quiz_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_users():
    with open(APP_DIR / "users.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ──────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="범죄심리학 퀴즈",
    page_icon="🔍",
    layout="centered"
)

# ──────────────────────────────────────────
# session_state 초기화
# ──────────────────────────────────────────
def init_state():
    defaults = {
        "logged_in": False,
        "username": "",
        "quiz_started": False,
        "current_q": 0,
        "score": 0,
        "answers": [],
        "per_question": {},
        "quiz_done": False,
        "show_explanation": False,
        "selected_choice": None,
        "has_scored_current": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ══════════════════════════════════════════
# 로그인 화면
# ══════════════════════════════════════════
def show_login():
    st.header("🔍 당신은 범인의 마음을 꿰뚫어 볼 수 있습니까?")
    st.markdown("##### 퀴즈를 풀어 당신의 프로파일링 능력을 테스트해보세요!")
    st.markdown("> 학번: 202610024, 이름: 최가빈")

    tab_login, tab_signup = st.tabs(["로그인", "회원가입"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("아이디")
            password = st.text_input("비밀번호", type="password")
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                submitted = st.form_submit_button("로그인", use_container_width=True)

        if submitted:
            users = load_users()
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"환영합니다, {username}님!")
                time.sleep(0.8)
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.") 
                
    with tab_signup:
        st.markdown("##### 새 계정을 만들고 퀴즈를 시작하세요.")
        with st.form("signup_form"):
            new_username = st.text_input("새 아이디")
            new_password = st.text_input("새 비밀번호", type="password")
            new_password2 = st.text_input("새 비밀번호 확인", type="password")
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                signup_submitted = st.form_submit_button("회원가입", use_container_width=True, type="primary")

        if signup_submitted:
            new_username = (new_username or "").strip()
            if not new_username:
                st.error("아이디를 입력해주세요.")
                return
            if not new_password:
                st.error("비밀번호를 입력해주세요.")
                return
            if new_password != new_password2:
                st.error("비밀번호와 비밀번호 확인이 일치하지 않습니다.")
                return

            users = load_users()
            if new_username in users:
                st.error("이미 존재하는 아이디입니다. 다른 아이디로 회원가입해주세요.")
                return

            users[new_username] = new_password
            try:
                with open(APP_DIR / "users.json", "w", encoding="utf-8") as f:
                    json.dump(users, f, ensure_ascii=False, indent=2)
            except Exception as e:
                st.error(f"회원가입 정보 저장 중 오류가 발생했습니다: {e}")
                return

            # 캐시 갱신 
            load_users.clear()
            st.success("회원가입이 완료되었습니다! 이제 로그인 탭에서 로그인해주세요.")

# ══════════════════════════════════════════
# 퀴즈 시작 화면
# ══════════════════════════════════════════
def show_intro():
    st.title("🔍 당신은 범인의 마음을 꿰뚫어 볼 수 있습니까?")
    st.markdown(f"**{st.session_state.username}**님, 반갑습니다! 다음 내용을 숙지한 뒤 퀴즈를 시작해주세요.")
    st.markdown("""
    - 범죄심리학 관련 개념과 실제 사건을 바탕으로 한 문제로 구성되어 있습니다.
    - 총 **11문제**이며 1번부터 10번까지 각 **1점**씩, 11번 문제는 **2점**이 주어집니다.
    - 각 문제 풀이 후 해설을 확인할 수 있습니다.
    - 퀴즈 시작 버튼을 눌러 당신의 능력을 테스트해보세요!
    """)

    if st.button("🚀 퀴즈 시작", use_container_width=True, type="primary"):
        st.session_state.quiz_started = True
        st.session_state.current_q = 0
        st.session_state.score = 0
        st.session_state.answers = []
        st.session_state.quiz_done = False
        st.rerun()

# ══════════════════════════════════════════
# 퀴즈 진행 화면
# ══════════════════════════════════════════
def show_quiz():
    quiz_data = load_quiz_data()  # 캐시에서 즉시 반환됨
    total = len(quiz_data)
    idx = st.session_state.current_q

    render_sidebar(quiz_data)

    if idx >= total:
        st.session_state.quiz_done = True
        st.rerun()
        return

    q = quiz_data[idx]

    # 진행률 표시
    st.progress((idx) / total, text=f"문제 {idx + 1} / {total}")
    st.markdown(f"### Q{idx + 1}. {q['question']}")

    if q.get("image"):
        try:
            img_path = Path(q["image"])
            if not img_path.is_absolute():
                img_path = APP_DIR / img_path
            st.image(str(img_path), use_container_width=True)
        except Exception:
            st.warning(f"이미지 파일을 불러올 수 없습니다: `{q['image']}`")

    # 선택지 표시: 가운데 정렬
    st.markdown(
        """
        <style>
          div[data-testid="column"] > div {display:flex; justify-content:center;}
          div[data-testid="stButton"] > button { white-space: pre-wrap; height: auto; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left, mid, right = st.columns([1, 3, 1])
    with mid:
        for opt_i, opt_text in enumerate(q["options"]):
            display_text = opt_text
            if q.get("id") == 11 and isinstance(opt_text, str) and "," in opt_text:
                display_text = ",\n".join([p.strip() for p in opt_text.split(",")])

            clicked = st.button(
                display_text,
                key=f"opt_{idx}_{opt_i}",
                use_container_width=True,
                disabled=st.session_state.show_explanation,
            )
            if clicked:
                st.session_state.selected_choice = opt_i
                st.session_state.show_explanation = True
                st.rerun()

    # 해설 표시 
    if st.session_state.show_explanation and st.session_state.selected_choice is not None:
        choice = st.session_state.selected_choice

        if not st.session_state.has_scored_current:
            is_correct = (choice == q["answer"])
            if is_correct:
                st.session_state.score += int(q.get("points", 1))
            st.session_state.per_question[idx] = is_correct

            my_answer_text = q["options"][choice]
            correct_text = q["options"][q["answer"]]

            st.session_state.answers.append(
                {
                    "question": q["question"],
                    "my_answer": my_answer_text,
                    "correct": correct_text,
                    "is_correct": is_correct,
                }
            )
            st.session_state.has_scored_current = True

        if choice == q["answer"]:
            st.success("✔ 정답입니다!")
        else:
            st.error(f"✘ 오답입니다. 정답: **{q['options'][q['answer']]}**")

        st.info(f"💡 해설: {q['explanation']}")

        _, mid2, _ = st.columns([1, 2, 1])
        with mid2:
            if st.button("▶ 다음 문제", use_container_width=True, type="primary"):
                st.session_state.current_q += 1
                st.session_state.show_explanation = False
                st.session_state.selected_choice = None
                st.session_state.has_scored_current = False
                st.rerun()

# ══════════════════════════════════════════
# 결과 화면
# ══════════════════════════════════════════
def show_result():
    quiz_data = load_quiz_data()
    total_points = sum(int(q.get("points", 1)) for q in quiz_data)
    score = st.session_state.score
    ratio = score / total_points 

    render_sidebar(quiz_data)

    st.title("최종 결과")

    if score >= 10:
        st.balloons()

    # 점수에 따른 유형 판별
    if score >= 10:
        profile = "🏆 FBI 수석 프로파일러"
        desc = "범죄심리학에 대한 탁월한 이해를 갖고 있습니다. 거의 완벽한 분석력!"
    elif score >= 7:
        profile = "🔎 <그것이 알고싶다> 마니아"
        desc = "범죄심리학 개념을 잘 파악하고 있습니다. 조금만 더 공부하면 전문가 수준!"
    elif score >= 4:
        profile = "👀 <명탐정 코난> 시청자"
        desc = "기본 개념은 알고 있지만 심화 내용까지는 아직이군요. 더 파고들어보세요!"
    else:
        profile = "🌱 프로파일러 꿈나무"
        desc = "아직 갈 길이 멀지만 이번 기회에 범죄심리학에 입문해보는 건 어떨까요?"

    st.markdown(f"## {profile}")
    st.markdown(f"**{score} / {total_points}점** — {desc}")
    st.progress(ratio)

    # 개념 설명 섹션
    st.markdown("---")
    st.markdown("### 범죄심리학 개념 정리")
    st.markdown("각 문제에서 다룬 실험·이론·개념을 확인해보세요.")

    for q in quiz_data:
        with st.expander(f"{q['question']}"):
            st.markdown("##### ✅ 정답/핵심")
            st.markdown(q["explanation"])
            st.markdown("##### 📚 세부 설명")
            st.markdown(q["detail"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 다시 도전", use_container_width=True, type="primary"):
            st.session_state.quiz_started = False
            st.session_state.quiz_done = False
            st.session_state.current_q = 0
            st.session_state.score = 0
            st.session_state.answers = []
            st.session_state.per_question = {}
            st.session_state.show_explanation = False
            st.session_state.selected_choice = None
            st.session_state.has_scored_current = False
            st.rerun()
    with col2:
        if st.button("🚪 로그아웃", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ══════════════════════════════════════════
# 라우팅
# ══════════════════════════════════════════
if not st.session_state.logged_in:
    show_login()
elif st.session_state.quiz_done:
    show_result()
elif st.session_state.quiz_started:
    show_quiz()
else:
    show_intro()