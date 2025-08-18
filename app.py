import os
import streamlit as st
from utils import run_agent_sync

st.set_page_config(page_title="MCP POC", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

st.title("Model Context Protocol(MCP) - Learning Path Generator")

# Built-in defaults: st.secrets -> environment variables -> DEFAULT_CONFIG
DEFAULT_CONFIG = {
    "GOOGLE_API_KEY": "AIzaSyBuGdRBKluYP-9Je1sDdVtl1c6n5IoQnFY",
    "YOUTUBE_PIPEDREAM_URL": "https://mcp.pipedream.net/7c2e475c-09c2-4bc9-bd3c-9c29438caf03/youtube_data_api",
    "DRIVE_PIPEDREAM_URL": "https://mcp.pipedream.net/7c2e475c-09c2-4bc9-bd3c-9c29438caf03/google_drive",
    "NOTION_PIPEDREAM_URL": "",
    "SECONDARY_TOOL": "Drive",
}

def get_config_value(key: str, fallback: str = "") -> str:
    try:
        value = None
        try:
            # st.secrets may not be configured; guard with try
            value = st.secrets.get(key, None)
        except Exception:
            value = None
        return (
            (value if value else None)
            or os.getenv(key)
            or DEFAULT_CONFIG.get(key, fallback)
            or ""
        )
    except Exception:
        return os.getenv(key) or DEFAULT_CONFIG.get(key, fallback) or ""

# Hide or show the entire configuration sidebar
HIDE_CONFIG_SIDEBAR = True if os.getenv("HIDE_CONFIG_SIDEBAR", "true").lower() == "true" else False

# Initialize session state for progress
if 'current_step' not in st.session_state:
    st.session_state.current_step = ""
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'last_section' not in st.session_state:
    st.session_state.last_section = ""
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False

if not HIDE_CONFIG_SIDEBAR:
    # Sidebar for API and URL configuration
    st.sidebar.header("Configuration")

    # API Key input (hidden when pre-configured)
    google_api_key_default = get_config_value("GOOGLE_API_KEY")
    if google_api_key_default:
        st.sidebar.caption("Using configured Google API key")
        if st.sidebar.checkbox("Change Google API Key", key="edit_google_api_key", value=False):
            google_api_key = st.sidebar.text_input(
                "Google API Key",
                value=google_api_key_default,
                type="password",
            )
        else:
            google_api_key = google_api_key_default
    else:
        google_api_key = st.sidebar.text_input(
            "Google API Key",
            placeholder="Enter your Google API Key",
            type="password",
        )

    # Pipedream URLs (hidden when pre-configured)
    st.sidebar.subheader("Pipedream URLs")
    youtube_default = get_config_value("YOUTUBE_PIPEDREAM_URL")
    if youtube_default:
        st.sidebar.caption("Using configured YouTube URL")
        if st.sidebar.checkbox("Change YouTube URL", key="edit_youtube_url", value=False):
            youtube_pipedream_url = st.sidebar.text_input(
                "YouTube URL (Required)",
                value=youtube_default,
                placeholder="Enter your Pipedream YouTube URL",
            )
        else:
            youtube_pipedream_url = youtube_default
    else:
        youtube_pipedream_url = st.sidebar.text_input(
            "YouTube URL (Required)",
            placeholder="Enter your Pipedream YouTube URL",
        )

    # Secondary tool selection (prefilled)
    tool_options = ["Drive", "Notion"]
    default_tool = get_config_value("SECONDARY_TOOL", "Drive")
    secondary_tool = st.sidebar.radio(
        "Select Secondary Tool:",
        tool_options,
        index=tool_options.index(default_tool) if default_tool in tool_options else 0,
    )

    # Secondary tool URL input (hidden when pre-configured)
    if secondary_tool == "Drive":
        drive_default = get_config_value("DRIVE_PIPEDREAM_URL")
        if drive_default:
            st.sidebar.caption("Using configured Drive URL")
            if st.sidebar.checkbox("Change Drive URL", key="edit_drive_url", value=False):
                drive_pipedream_url = st.sidebar.text_input(
                    "Drive URL",
                    value=drive_default,
                    placeholder="Enter your Pipedream Drive URL",
                )
            else:
                drive_pipedream_url = drive_default
        else:
            drive_pipedream_url = st.sidebar.text_input(
                "Drive URL",
                placeholder="Enter your Pipedream Drive URL",
            )
        notion_pipedream_url = None
    else:
        notion_default = get_config_value("NOTION_PIPEDREAM_URL")
        if notion_default:
            st.sidebar.caption("Using configured Notion URL")
            if st.sidebar.checkbox("Change Notion URL", key="edit_notion_url", value=False):
                notion_pipedream_url = st.sidebar.text_input(
                    "Notion URL",
                    value=notion_default,
                    placeholder="Enter your Pipedream Notion URL",
                )
            else:
                notion_pipedream_url = notion_default
        else:
            notion_pipedream_url = st.sidebar.text_input(
                "Notion URL",
                placeholder="Enter your Pipedream Notion URL",
            )
        drive_pipedream_url = None
else:
    # Use only configured values; no sidebar widgets
    google_api_key = get_config_value("GOOGLE_API_KEY")
    youtube_pipedream_url = get_config_value("YOUTUBE_PIPEDREAM_URL")
    secondary_tool = get_config_value("SECONDARY_TOOL", "Drive")
    if secondary_tool == "Drive":
        drive_pipedream_url = get_config_value("DRIVE_PIPEDREAM_URL")
        notion_pipedream_url = None
    else:
        notion_pipedream_url = get_config_value("NOTION_PIPEDREAM_URL")
        drive_pipedream_url = None

# Quick guide before goal input
if not HIDE_CONFIG_SIDEBAR:
    st.info("""
**Quick Guide:**
1. Enter your Google API key and YouTube URL (required)
2. Select and configure your secondary tool (Drive or Notion)
3. Enter a clear learning goal, for example:
    - "I want to learn python basics in 3 days"
    - "I want to learn data science basics in 10 days"
""")
else:
    st.info("""
**Quick Guide:**
1. Configuration is preloaded from secrets, environment variables, or DEFAULT_CONFIG
2. Enter a clear learning goal, for example:
    - "I want to learn python basics in 3 days"
    - "I want to learn data science basics in 10 days"
""")

# Main content area
st.header("Enter Your Goal")
user_goal = st.text_input("Enter your learning goal:",
                        help="Describe what you want to learn, and we'll generate a structured path using YouTube content and your selected tool.")

# Progress area
progress_container = st.container()
progress_bar = st.empty()

def update_progress(message: str):
    """Update progress in the Streamlit UI"""
    st.session_state.current_step = message
    
    # Track previous section to detect changes
    previous_section = st.session_state.last_section
    
    # Determine section and update progress
    if "Setting up agent with tools" in message:
        section = "Setup"
        st.session_state.progress = 0.1
    elif "Added Google Drive integration" in message or "Added Notion integration" in message:
        section = "Integration"
        st.session_state.progress = 0.2
    elif "Creating AI agent" in message:
        section = "Setup"
        st.session_state.progress = 0.3
    elif "Generating your learning path" in message:
        section = "Generation"
        st.session_state.progress = 0.5
    elif "Learning path generation complete" in message:
        section = "Complete"
        st.session_state.progress = 1.0
        st.session_state.is_generating = False
    else:
        section = st.session_state.last_section or "Progress"
    
    # Show progress bar
    progress_bar.progress(st.session_state.progress)
    
    # Update progress container with current status
    with progress_container:
        # Show section header if it changed
        if section != previous_section and section != "Complete":
            st.write(f"**{section}**")
        
        # Show message with tick for completed steps
        if message == "Learning path generation complete!":
            st.success("All steps completed! 🎉")
        else:
            prefix = "✓" if st.session_state.progress >= 0.5 else "→"
            st.write(f"{prefix} {message}")
    
    # Update last section after rendering
    st.session_state.last_section = section

# Generate Learning Path button
if st.button("Generate Learning Path", type="primary", disabled=st.session_state.is_generating):
    if not google_api_key:
        st.error("Google API key is required. Configure via secrets, environment variable, or DEFAULT_CONFIG.")
    elif not youtube_pipedream_url:
        st.error("YouTube URL is required. Configure via secrets, environment variable, or DEFAULT_CONFIG.")
    elif (secondary_tool == "Drive" and not drive_pipedream_url) or (secondary_tool == "Notion" and not notion_pipedream_url):
        st.error(f"{secondary_tool} URL is required. Configure via secrets, environment variable, or DEFAULT_CONFIG.")
    elif not user_goal:
        st.warning("Please enter your learning goal.")
    else:
        try:
            # Set generating flag
            st.session_state.is_generating = True
            
            # Reset progress
            st.session_state.current_step = ""
            st.session_state.progress = 0
            st.session_state.last_section = ""
            
            result = run_agent_sync(
                google_api_key=google_api_key,
                youtube_pipedream_url=youtube_pipedream_url,
                drive_pipedream_url=drive_pipedream_url,
                notion_pipedream_url=notion_pipedream_url,
                user_goal=user_goal,
                progress_callback=update_progress
            )
            
            # Display results
            st.header("Your Learning Path")
            displayed = False
            if isinstance(result, dict):
                if "messages" in result and result["messages"]:
                    for msg in result["messages"]:
                        content = getattr(msg, "content", msg)
                        st.markdown(f"📚 {content}")
                    displayed = True
                elif "output" in result:
                    st.markdown(str(result["output"]))
                    displayed = True

            if not displayed:
                content = getattr(result, "content", None)
                if content:
                    st.markdown(f"📚 {content}")
                    displayed = True

            if not displayed:
                st.json(result)
                st.session_state.is_generating = False
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please check your API keys and URLs, and try again.")
            st.session_state.is_generating = False
