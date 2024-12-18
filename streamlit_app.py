# project_root/ui/streamlit_app.py

import streamlit as st
import asyncio
from orchestrator.orchestrator import AppBuilderOrchestrator

st.set_page_config(page_title="Autonomous App Builder", layout="wide")

st.title("Autonomous App Builder")

user_input = st.text_area("Enter your project requirements:", 
                          "I want a task management PWA with React frontend, a Python Flask backend, and a SwiftUI iOS app.")

if st.button("Start Building"):
    if user_input.strip():
        st.write("Starting the application build process...")
        orchestrator = AppBuilderOrchestrator()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(orchestrator.build_app(user_input))
            st.success("Application built and deployed successfully!")
        except Exception as e:
            st.error(f"Application build/deployment failed: {e}")
    else:
        st.warning("Please enter your project requirements to proceed.")