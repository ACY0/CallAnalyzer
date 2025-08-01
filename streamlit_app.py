import streamlit as st
import pandas as pd

st.set_page_config(page_title="Call Center Analyzer", layout="wide")
st.title("📊 Call Center Log Analyzer")

uploaded_file = st.file_uploader("📂 Upload your Excel file (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0)
        df.columns = df.columns.str.strip().str.lower()  # clean & lowercase column names

        st.write("✅ Columns detected:", df.columns.tolist())

        required_cols = ["state", "date", "start time"]
        for col in required_cols:
            if col not in df.columns:
                st.error(f"❌ Required column missing: '{col}'")
                st.stop()

        df["date"] = pd.to_datetime(df["date"])
        df_sorted = df.sort_values(by=["date", "start time"], ascending=[True, True])

        results = []
        for date, group in df_sorted.groupby(df_sorted["date"].dt.date):
            # ✅ Lowercase compare for safety
            available_rows = group[group["state"].str.lower() == "available"]
            if not available_rows.empty:
                first_avail_time = pd.to_datetime(available_rows.iloc[0]["start time"]).time()
                results.append({"Date": date, "First Available": first_avail_time})

        result_df = pd.DataFrame(results)
        st.subheader("📅 First 'Available' Time Per Day")
        st.dataframe(result_df)

    except Exception as e:
        st.error("🚨 An error occurred while processing the file:")
        st.exception(e)
else:
    st.info("⬆️ Please upload an Excel file to begin.")
