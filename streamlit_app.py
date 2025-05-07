import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import calplot
from matplotlib import colors
import os

API_URL = os.getenv("FLASK_API_URL", "http://localhost:5000")

st.title("🗓️ Daily Task Tracker")

if "user_id" not in st.session_state:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        res = requests.post("http://localhost:5000/login", json={"username": username, "password": password})
        if res.status_code == 200:
            st.session_state.user_id = res.json()["user_id"]
            st.success("Logged in successfully")
            st.rerun()
        else:
            st.error("Login failed")
    if st.button("Register"):
        reg = requests.post("http://localhost:5000/register", json={"username": username, "password": password})
        if reg.status_code == 200:
            st.success("Registered! Now login.")
        else:
            st.error("User already exists")
else:
    st.subheader("Your Tasks")
    user_id = st.session_state.user_id

    tasks = requests.get("http://localhost:5000/get_tasks", params={"user_id": user_id}).json()
    today = datetime.today().strftime("%Y-%m-%d")

    for task in tasks:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(task["task_name"])
        with col2:
            current_status = task["history"].get(today, "no")
            status = st.radio("", ["yes", "no"], index=["yes", "no"].index(current_status), key=task["_id"])

        # Date picker to select date (defaults to today's date)
        selected_date = st.date_input("Select Date", value=datetime.today(), key=f"date_{task['_id']}")

        if st.button(f"Update {task['task_name']}", key=f"update_{task['_id']}"):
            requests.post("http://localhost:5000/update_task", json={
                "user_id": user_id,
                "task_name": task["task_name"],
                "date": selected_date.strftime("%Y-%m-%d"),
                "status": status
            })
            st.success(f"Task {task['task_name']} updated for {selected_date.strftime('%Y-%m-%d')}")
            st.rerun()

        # Display the heatmap for each task only if "yes" status is present
        st.subheader(f"📊 Heatmap for {task['task_name']}")
        try:
            history = task["history"]
            if history:
                # Filter out only dates that have "yes" status
                valid_dates = [date for date, value in history.items() if value == "yes"]
                values = [1 for _ in valid_dates]  # Only show 1 for "yes" status
                dates = pd.to_datetime(valid_dates)
                series = pd.Series(values, index=dates)

                # Custom dark red colormap
                dark_red_cmap = colors.ListedColormap(['#f82f04', '#FFFFFF'])  # From white (#FFFFFF) to dark red (#f82f04)

                # Plot the heatmap only if we have valid "yes" statuses
                if len(series) > 0:  # Check if the series is not empty
                    calplot.calplot(series, cmap=dark_red_cmap, figsize=(8, 2))
                    st.pyplot(plt.gcf())

                    # Graph
                    valid_dates = [date for date, value in history.items() if value in ["yes", "no"]]
                    values = [1 if history[date] == "yes" else 0 for date in valid_dates]  # "1" for "yes", "0" for "no"
                    dates = pd.to_datetime(valid_dates)
                    
                    # Create a DataFrame for task status over days
                    task_status_df = pd.DataFrame({
                        "Date": dates,
                        "Status": values
                    })
                    task_status_df.set_index("Date", inplace=True)

                    # Plot the task status vs. date
                    st.subheader(f"📈 Task Status Over Time for {task['task_name']}")
                    task_status_df["Moving Average"] = task_status_df["Status"].rolling(window=3).mean()
                    st.line_chart(task_status_df[["Status", "Moving Average"]])
                
                else:
                    st.info(f"No 'yes' status for {task['task_name']}")
            else:
                st.info(f"No data to show for {task['task_name']}")
        except Exception as e:
            st.error(f"Error displaying heatmap for {task['task_name']}: {e}")
