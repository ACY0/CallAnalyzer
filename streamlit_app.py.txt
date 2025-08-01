import streamlit as st
import pandas as pd

def duration_to_seconds(t):
    try:
        h, m, s = map(int, t.strip().split(":"))
        return h*3600 + m*60 + s
    except:
        return 0

st.title("📊 Call Center Analyzer")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0)

    df["DurationSeconds"] = df["Duration"].astype(str).apply(duration_to_seconds)
    df["Date"] = df["Date"].astype(str)

    st.success("Data loaded successfully!")

    result = {
        "Geç Giriş": 0,
        "Erken Mola (1 saat içinde Break)": 0,
        "Erken Çıkış (<16:25)": 0,
        "Kısa Meeting/Training (<15dk)": 0,
        "Break Süresi > 15 dk": 0,
        "Günlük Break > 1 saat": 0,
    }

    unique_dates = df["Date"].unique()

    for date in unique_dates:
        day_data = df[df["Date"] == date].iloc[::-1]
        available_rows = day_data[day_data["State"] == "Available"]
        break_rows = day_data[day_data["State"] == "Break"]
        logout_rows = day_data[day_data["State"] == "Logged Out"]

        if not available_rows.empty:
            first_avail_time = pd.to_datetime(available_rows.iloc[0]["Start tme"]).time()
            if first_avail_time > pd.to_datetime("07:45:00").time():
                result["Geç Giriş"] += 1

            for i, row in break_rows.iterrows():
                break_time = pd.to_datetime(row["Start tme"]).time()
                if break_time <= (pd.to_datetime(first_avail_time.strftime("%H:%M:%S")) + pd.Timedelta(hours=1)).time():
                    result["Erken Mola (1 saat içinde Break)"] += 1
                    break

        if not logout_rows.empty:
            last_logout_time = pd.to_datetime(logout_rows.iloc[0]["Start tme"]).time()
            after_logout = available_rows[available_rows["Start tme"] > logout_rows.iloc[0]["Start tme"]]
            if last_logout_time < pd.to_datetime("16:25:00").time() and after_logout.empty:
                result["Erken Çıkış (<16:25)"] += 1

        short_mt = df[(df["Date"] == date) & (df["State"].isin(["Meeting", "Training"])) & (df["DurationSeconds"] < 900)]
        result["Kısa Meeting/Training (<15dk)"] += len(short_mt)

        long_breaks = df[(df["Date"] == date) & (df["State"] == "Break") & (df["DurationSeconds"] > 900)]
        result["Break Süresi > 15 dk"] += len(long_breaks)

        total_break = df[(df["Date"] == date) & (df["State"] == "Break")]["DurationSeconds"].sum()
        if total_break > 3600:
            result["Günlük Break > 1 saat"] += 1

    st.subheader("📋 Analysis Summary")
    st.dataframe(pd.DataFrame(result.items(), columns=["Kategori", "Sayı"]))
