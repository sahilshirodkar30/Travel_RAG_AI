"""Streamlit app: Google sign-in (L1), chat, and an admin review tab (L6). It only calls handle_question()."""
import sys
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # make 'app' and 'services' importable

import streamlit as st

from app.agent.graph import handle_question
from app.config import get_settings
from app.hitl.review_queue import decide, pending
from app.observability import setup_observability

st.set_page_config(page_title="Goa Travel Guide", page_icon="🌴")


@st.cache_resource  # runs once per server process
def _boot() -> bool:
    setup_observability()
    return True


_boot()


def current_user() -> dict | None:
    """Return the signed-in user with a role, or None if nobody is signed in.
    Google tells us who the person is. Our admin list decides what they can do."""
    if not st.user.is_logged_in:
        return None
    email = (st.user.email or "").lower()
    role = "admin" if email in get_settings().admin_email_set else "user"
    return {"name": st.user.name or email, "email": email, "role": role}


def _logout() -> None:
    st.session_state.clear()  # drop chat history so the next person starts fresh
    st.logout()


def login_screen() -> None:
    st.title("🌴 Goa Travel Guide")
    st.write("Sign in with your Google account to ask questions about Goa.")
    st.button("Sign in with Google", on_click=st.login)


def chat_tab(user: dict) -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = uuid.uuid4().hex  # one LangGraph thread per session

    for m in st.session_state.messages:
        st.chat_message(m["role"]).write(m["content"])

    question = st.chat_input("Ask about Goa: beaches, food, festivals, transport...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner("Planning..."):
            result = handle_question(user["email"], question, st.session_state.thread_id)
        text = result["answer"]
        if result["sources"]:
            text += "\n\n_Sources: " + ", ".join(result["sources"]) + "_"
        st.session_state.messages.append({"role": "assistant", "content": text})
        st.session_state.history_count = result["history_count"]
        st.rerun()

    st.sidebar.metric("Questions in this chat", st.session_state.get("history_count", 0))


def review_tab() -> None:
    items = pending()
    if not items:
        st.info("Nothing waiting for review.")
    for item in items:
        with st.expander(item["question"]):
            st.caption("Sources: " + ", ".join(item["sources"]))
            edited = st.text_area("Answer", item["draft"], key=f"txt-{item['id']}")
            c1, c2 = st.columns(2)
            if c1.button("Approve", key=f"ok-{item['id']}"):
                decide(item["id"], True, edited)
                st.rerun()
            if c2.button("Reject", key=f"no-{item['id']}"):
                decide(item["id"], False)
                st.rerun()


def main() -> None:
    user = current_user()
    if user is None:
        login_screen()
        st.stop()

    st.sidebar.write(f"Signed in as **{user['name']}**")
    st.sidebar.caption(user["email"])
    st.sidebar.button("Log out", on_click=_logout)

    # L1 authorization: only admins see the review queue
    if user["role"] == "admin":
        chat, review = st.tabs(["Ask Goa", "Review queue"])
        with chat:
            chat_tab(user)
        with review:
            review_tab()
    else:
        chat_tab(user)


main()