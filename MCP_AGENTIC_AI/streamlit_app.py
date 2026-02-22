from pathlib import Path
import pandas as pd
import streamlit as st
import requests
import json
import plotly.io as pio
import uuid
from logger.base_logger import get_logger

logger = get_logger(__name__)

API_URL = "http://127.0.0.1:6000"
DEFAULT_USER = "Soundarya"
DEFAULT_USER_ID = 1


# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Smart Agent",
    layout="wide"
)


# =========================
# Session Initialization
# =========================
def create_session():
    """Create a new chat session from backend"""
    payload = {"user_id": DEFAULT_USER_ID}
    res = requests.post(f"{API_URL}/new_session", json=payload)

    if res.status_code != 200:
        st.error("❗ Failed to create chat session")
        st.stop()

    data = res.json()
    st.session_state.chat_session_id = data["chat_session_id"]
    logger.info(f"New chat session created: {data}")


def init_session():
    """Initialize session only on first load"""
    if "chat_initialized" not in st.session_state:
        create_session()
        st.session_state.chat_initialized = True

    if "messages" not in st.session_state:
        st.session_state.messages = []


init_session()


# =========================
# Centered Title
# =========================
st.markdown(
    f"""
    <h1 style='text-align: center;'>
        🤖 Welcome {DEFAULT_USER}!
    </h1>
    <p style='text-align: center; font-size:18px; color:gray;'>
        Smart City Assistant
    </p>
    """,
    unsafe_allow_html=True
)


# =========================
# Block Renderer
# =========================
def render_block(block: dict):
    """Render response blocks"""

    block_type = block.get("type")

    # ---------- MARKDOWN ----------
    if block_type == "markdown":
        st.markdown(block.get("content", ""))

    # ---------- CSV ----------
    elif block_type == "csv":
        filepath = block.get("filepath")

        if filepath and Path(filepath).exists():
            path = Path(filepath)

            df = pd.read_csv(path)

            st.dataframe(df.head(), width="stretch")
            st.caption(
                f"Showing first 5 rows • {df.shape[0]} rows × {df.shape[1]} columns"
            )

            with open(path, "rb") as f:
                button_key = f"download_{path.name}_{uuid.uuid4()}"

                st.download_button(
                    label="⬇️ Download CSV",
                    data=f,
                    mime="text/csv",
                    key=button_key
                )
        else:
            st.warning(f"CSV file not found: {filepath}")

    # ---------- PLOTLY ----------
    elif block_type == "plotly_plot_json":
        filepath = block.get("filepath")

        if filepath and Path(filepath).exists():
            path = Path(filepath)

            try:
                fig = pio.from_json(path.read_text())
                st.plotly_chart(fig, width="stretch")
            except Exception as e:
                st.error(f"Error rendering plot: {e}")

        else:
            st.warning(f"Plot file not found: {filepath}")

    elif block_type in ["text", "document"]:
        filepath = block.get("filepath")

        if filepath and Path(filepath).exists():
            path = Path(filepath)

            try:
                suffix = path.suffix.lower()

                if suffix in [".txt", ".md", ".json", ".log", ".csv"]:
                    content = path.read_text(errors="ignore")

                    preview = content[:2000]  # limit preview size
                    st.text_area(
                        "Preview",
                        preview,
                        height=300,
                        key=f"preview_{path.name}"
                    )

                elif suffix == ".pdf":
                    st.info("PDF preview not supported inline. Please download.")

                # ---------- DOCX ----------
                elif suffix == ".docx":
                    st.info("DOCX preview not supported inline. Please download.")

                else:
                    st.info(f"Preview not supported for {suffix} files.")

                # ---------- DOWNLOAD BUTTON ----------
                with open(path, "rb") as f:
                    button_key = f"download_{path.name}_{uuid.uuid4()}"

                    st.download_button(
                        label="⬇️ Download File",
                        data=f,
                        file_name=path.name,
                        key=button_key
                    )

            except Exception as e:
                st.error(f"Error rendering file: {e}")

        else:
            st.warning(f"File not found: {filepath}")
            
    # ---------- UNKNOWN ----------
    else:
        st.info(f"Unsupported block type: {block_type}")


# =========================
# Render Chat History
# =========================
for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        blocks = msg.get("content", [])

        if isinstance(blocks, str):
            blocks = [{"type": "markdown", "content": blocks}]

        for block in blocks:
            render_block(block)
            st.divider()


# =========================
# Chat Input
# =========================
prompt = st.chat_input(f"Ask me anything, {DEFAULT_USER}...")

if prompt:

    # ---------- Store User Message ----------
    user_blocks = [{"type": "markdown", "content": prompt}]

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_blocks,
        }
    )

    with st.chat_message("user"):
        render_block(user_blocks[0])

    # ---------- API Call ----------
    payload = {
        "user_id": DEFAULT_USER_ID,
        "chat_session_id": st.session_state.chat_session_id,
        "user_query": prompt,
    }

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:
                res = requests.post(f"{API_URL}/chat", json=payload)

                if res.status_code == 200:
                    reply = res.json().get("response", [])
                else:
                    reply = [
                        {
                            "type": "markdown",
                            "content": "❗ Unable to get response from server.",
                        }
                    ]

            except Exception as e:
                logger.error(e)
                reply = [
                    {
                        "type": "markdown",
                        "content": "❗ Server connection error.",
                    }
                ]

            # ---------- Normalize ----------
            if isinstance(reply, str):
                try:
                    reply = json.loads(reply)
                except Exception:
                    reply = [{"type": "markdown", "content": reply}]

            # ---------- Render ----------
            for block in reply:
                render_block(block)
                st.divider()

            # ---------- Store ----------
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": reply,
                }
            )