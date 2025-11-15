# app.py — Pareto To Do Agent (Streamlit)
import streamlit as st
import requests
from openai import OpenAI
from datetime import datetime, timedelta

st.set_page_config(page_title="Pareto AI", page_icon="rocket", layout="centered")
st.title("Pareto To Do Agent")
st.markdown("**80% results with 20% effort**")

# === SIDEBAR SETUP ===
with st.sidebar:
    st.header("Setup")
    XAI_API_KEY = st.text_input("xAI API Key", type="password", help="Get from https://x.ai/api")
    TASK_LIST_ID = st.text_input("To Do List ID", help="From Graph Explorer")
    st.caption("Need help? Scroll down.")

if not XAI_API_KEY or not TASK_LIST_ID:
    st.info("Enter your keys in the sidebar to start.")
    st.stop()

# === MAIN APP ===
goal = st.text_input("Your Goal", placeholder="e.g., Grow email list to 1000")

if st.button("Generate Pareto Tasks", type="primary"):
    if not goal:
        st.error("Enter a goal.")
    else:
        with st.spinner("Thinking with Grok AI..."):
            try:
                client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")
                prompt = f"""
                Goal: {goal}
                Apply Pareto: 20% effort → 80% results.
                Return 3–5 tasks as:
                1. Title - Description with [ ] checklist
                """
                response = client.chat.completions.create(
                    model="grok-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                steps = response.choices[0].message.content.strip()
                st.session_state.steps = steps
                st.success("Done!")
                st.markdown("### Tasks:")
                st.code(steps)
            except Exception as e:
                st.error(f"AI Error: {e}")

# === CREATE TASKS BUTTON ===
if "steps" in st.session_state:
    if st.button("Create in Microsoft To Do", type="primary"):
        with st.spinner("Logging in to Microsoft..."):
            auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode"
            r = requests.post(auth_url, data={
                "client_id": "d3590ed6-52b3-4102-aeff-aad2292ab01c",
                "scope": "Tasks.ReadWrite offline_access"
            })
            resp = r.json()
            st.info(f"Go to: [{resp['verification_uri']}]({resp['verification_uri']})\nCode: `{resp['user_code']}`")
            if st.button("I signed in → Continue"):
                token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
                while True:
                    t = requests.post(token_url, data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        "client_id": "d3590ed6-52b3-4102-aeff-aad2292ab01c",
                        "device_code": resp['device_code']
                    })
                    token = t.json()
                    if "access_token" in token:
                        access_token = token["access_token"]
                        st.success("Connected!")
                        break
                    elif token.get("error") != "authorization_pending":
                        st.error("Login failed.")
                        st.stop()

        # Create tasks
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT10:00:00")
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        tasks = []
        for line in st.session_state.steps.split("\n"):
            if line.strip() and line[0].isdigit():
                parts = line.split("-", 1)
                if len(parts) == 2:
                    title = parts[0].strip()[2:].strip()
                    desc = parts[1].strip()
                    tasks.append((title, desc))

        for title, desc in tasks:
            payload = {
                "title": title,
                "body": {"content": desc, "contentType": "text"},
                "importance": "high",
                "dueDateTime": {"dateTime": tomorrow, "timeZone": "Eastern Standard Time"},
                "reminderDateTime": {"dateTime": tomorrow.replace("10:00", "09:00"), "timeZone": "Eastern Standard Time"},
                "isReminderOn": True,
                "categories": ["Pareto-80/20"]
            }
            url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{TASK_LIST_ID}/tasks"
            r = requests.post(url, headers=headers, json=payload)
            if r.status_code == 201:
                st.success(f"Created: {title}")
            else:
                st.error(f"Failed: {title}")

        st.balloons()
        st.markdown("### All tasks created in Microsoft To Do!")

# === FOOTER ===
st.markdown("---")
st.caption("Built for mobile • Free • Private • Powered by Grok AI")
