import asyncio

import streamlit as st
from google import genai
from google.genai import types
from telegram import Bot

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT,
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Deadline Tracker AI",
    page_icon="📅",
    layout="centered",
)


# ==================================================
# CONFIGURATION
# ==================================================

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = str(st.secrets["TELEGRAM_CHAT_ID"])

# Working model
MODEL_NAME = "gemini-3.5-flash-lite"


# ==================================================
# CLIENTS
# ==================================================

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


@st.cache_resource
def get_telegram_bot():
    return Bot(token=TELEGRAM_BOT_TOKEN)


gemini_client = get_gemini_client()
telegram_bot = get_telegram_bot()


# ==================================================
# TELEGRAM
# ==================================================

def send_telegram(message):
    try:
        asyncio.run(
            telegram_bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
            )
        )

        return True, "Message sent successfully."

    except Exception as error:
        return False, str(error)


# ==================================================
# GEMINI CHAT
# ==================================================

def create_chat():
    return gemini_client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        ),
    )


def ask_gemini(parts):
    try:
        response = st.session_state.chat.send_message(parts)

        if response.text:
            return response.text

        return "I couldn't generate a response for that."

    except Exception as error:
        return f"Sorry, something went wrong: {error}"


# ==================================================
# MESSAGE HANDLING
# ==================================================

def add_message(role, kind, content):
    message = {
        "role": role,
        "kind": kind,
        "content": content,
    }

    st.session_state.messages.append(message)


def render_message(message):
    with st.chat_message(message["role"]):

        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


# ==================================================
# SESSION STATE
# ==================================================

if "onboarded" not in st.session_state:
    st.session_state.onboarded = False


# ==================================================
# ONBOARDING
# ==================================================

if not st.session_state.onboarded:

    st.title("📅 Deadline Tracker AI")

    st.caption(
        "AI-Powered Academic Deadline Assistant"
    )

    st.write(
        "Upload your academic schedule, syllabus, "
        "assignment sheet, exam timetable, or notice "
        "and let AI find the important deadlines."
    )

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your name",
            placeholder="Enter your name",
        )

        submitted = st.form_submit_button(
            "Let's get started 🚀"
        )

    if submitted:

        if not name.strip():

            st.warning("Please enter your name.")

        else:

            st.session_state.name = name.strip()

            st.session_state.chat = create_chat()

            st.session_state.messages = []

            st.session_state.onboarded = True

            st.rerun()

    st.stop()


# ==================================================
# FLOATING TELEGRAM BUTTON
# ==================================================

st.markdown(
    """
    <style>

    /* Floating Telegram button container */
    div[data-testid="stButton"] {
        position: fixed !important;
        top: 18px !important;
        right: 24px !important;

        width: 190px !important;
        min-width: 190px !important;
        max-width: 190px !important;

        z-index: 999999 !important;

        margin: 0 !important;
        padding: 0 !important;
    }

    /* Actual Telegram button */
    div[data-testid="stButton"] button {
        width: 190px !important;
        min-width: 190px !important;
        max-width: 190px !important;

        height: 44px !important;

        border-radius: 10px !important;

        font-weight: 600 !important;

        white-space: nowrap !important;

        box-shadow:
            0 4px 16px rgba(0, 0, 0, 0.35) !important;
    }

    /* Prevent overlap on smaller screens */
    @media (max-width: 700px) {

        div[data-testid="stButton"] {
            top: 10px !important;
            right: 10px !important;

            width: 170px !important;
            min-width: 170px !important;
            max-width: 170px !important;
        }

        div[data-testid="stButton"] button {
            width: 170px !important;
            min-width: 170px !important;
            max-width: 170px !important;

            height: 40px !important;

            font-size: 0.85rem !important;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# TELEGRAM ACTION
# ==================================================

send_disabled = len(st.session_state.messages) == 0

if st.button(
    "📤 Send to Telegram",
    disabled=send_disabled,
):

    with st.spinner(
        "Preparing your deadline digest..."
    ):

        summary = ask_gemini(
            [SUMMARY_REQUEST_PROMPT]
        )

    success, info = send_telegram(summary)

    if success:

        st.success(
            "Deadline digest sent to Telegram! 📲"
        )

    else:

        st.error(
            f"Couldn't send the message: {info}"
        )


# ==================================================
# MAIN HEADER
# ==================================================

st.title("📅 Deadline Tracker AI")

st.caption(
    "AI-Powered Academic Deadline Assistant"
)

st.caption(
    f"Logged in as {st.session_state.name}"
)


# ==================================================
# CHAT HISTORY
# ==================================================

if not st.session_state.messages:

    welcome_message = (
        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        )
    )

    add_message(
        "assistant",
        "text",
        welcome_message,
    )


for message in st.session_state.messages:

    render_message(message)


# ==================================================
# CHAT INPUT + IMAGE UPLOAD
# ==================================================

user_input = st.chat_input(
    "Ask about a deadline or upload a schedule...",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png",
    ],
)


if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []


    # ----------------------------------------------
    # IMAGE
    # ----------------------------------------------

    if photo is not None:

        photo_bytes = photo.getvalue()

        add_message(
            "user",
            "image",
            photo_bytes,
        )

        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type,
            )
        )


    # ----------------------------------------------
    # TEXT
    # ----------------------------------------------

    if text:

        add_message(
            "user",
            "text",
            text,
        )

        parts.append(text)


    # ----------------------------------------------
    # IMAGE-ONLY REQUEST
    # ----------------------------------------------

    elif photo is not None:

        parts.append(
            """
            Analyze this academic image and extract
            all clearly visible:

            - deadlines
            - assignments
            - exams
            - projects
            - submission dates
            - important academic dates

            For every item, provide:

            Task:
            Subject:
            Date:
            Time:
            Notes:

            Do not guess missing information.
            If something is unclear, clearly say so.
            """
        )


    # ----------------------------------------------
    # GEMINI RESPONSE
    # ----------------------------------------------

    if parts:

        with st.spinner(
            "Reading your academic schedule... 🔎"
        ):

            answer = ask_gemini(parts)


        add_message(
            "assistant",
            "text",
            answer,
        )

        st.rerun()