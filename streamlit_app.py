import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Sayfa ayarları
st.set_page_config(page_title="CC Agent Telephony Performance Analysis", layout="wide")
st.title("📊 Agent Telephony Performance Analysis")


# Excel dosyası yükleyici
uploaded_file = st.file_uploader("📂 Upload your Excel file (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0)
        df.columns = df.columns.str.strip().str.lower()  # Sütun adlarını temizle

        st.write("✅ Columns detected:", df.columns.tolist())

        required_cols = ["state", "date", "start time", "duration"]
        for col in required_cols:
            if col not in df.columns:
                st.error(f"❌ Required column missing: '{col}'")
                st.stop()

        # Tarih ve saatleri düzenle
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["start time"] = pd.to_datetime(df["start time"].astype(str), errors='coerce').dt.time

        # Duration'ı saniyeye çevir
        def duration_to_seconds(d):
            try:
                t = str(d).strip()
                if pd.isna(t) or t == "":
                    return 0
                parts = list(map(int, t.split(":")))
                if len(parts) == 3:
                    return parts[0]*3600 + parts[1]*60 + parts[2]
                elif len(parts) == 2:
                    return parts[0]*60 + parts[1]
                else:
                    return 0
            except:
                return 0

        df["duration_sec"] = df["duration"].apply(duration_to_seconds)

        # Tarihe göre sırala
        df_sorted = df.sort_values(by=["date", "start time"], ascending=[True, True])

        # Fail listeleri
        late_entry = []
        early_break = []
        early_logout = []
        break_fail = []
        break_over_1h = []
        short_meeting = []

        # Gün gün analiz et
        for date, group in df_sorted.groupby("date"):
            group = group.reset_index(drop=True)

            # Geç Giriş
            availables = group[group["state"].str.lower() == "available"]
            if not availables.empty:
                first_avail_time = availables.iloc[0]["start time"]
                if first_avail_time > datetime.strptime("07:45:00", "%H:%M:%S").time():
                    late_entry.append((date, first_avail_time))

            # Erken Mola (login'den sonraki ilk 1 saat içinde break)
            if not availables.empty:
                first_time = datetime.combine(datetime.today(), availables.iloc[0]["start time"])
                break_found = group[group["state"].str.lower() == "break"]
                for _, row in break_found.iterrows():
                    current_time = datetime.combine(datetime.today(), row["start time"])
                    if timedelta(0) <= current_time - first_time <= timedelta(hours=1):
                        early_break.append((date, row["start time"], row["duration_sec"]))
                        break

            # Erken Çıkış
            logouts = group[group["state"].str.lower() == "logged out"]
            if not logouts.empty:
                last_logout = logouts.iloc[-1]
                last_time = last_logout["start time"]
                after_logout = group[group["start time"] > last_time]
                if not any(after_logout["state"].str.lower().str.contains("available")):
                    if last_time < datetime.strptime("16:25:00", "%H:%M:%S").time():
                        early_logout.append((date, last_time))

            # Uzun Break (satır bazlı > 15dk)
            for _, row in group.iterrows():
                if row["state"].lower() == "break" and row["duration_sec"] > 900:
                    break_fail.append((date, row["start time"], row["duration_sec"]))

            # Günlük toplam break > 1 saat
            total_break = group[group["state"].str.lower() == "break"]["duration_sec"].sum()
            if total_break > 3600:
                break_over_1h.append((date, total_break))

            # Kısa Meeting / Training (<15dk)
            for _, row in group.iterrows():
                if row["state"].lower() in ["meeting", "training"] and 0 < row["duration_sec"] < 900:
                    short_meeting.append((date, row["start time"], row["duration_sec"]))

        # Özet tablo
        st.subheader("📊 Failure Analysis Summary")
        st.dataframe(pd.DataFrame({
            "Kategori": [
                "Geç Giriş",
                "Erken Mola (İlk 1 saat içinde Break)",
                "Erken Çıkış (16:25’ten önce)",
                "Break Süresi > 15 dk (satır bazlı)",
                "Günlük Break Süresi > 1 saat",
                "Kısa Meeting/Training (<15dk)"
            ],
            "Sayı": [
                len(late_entry),
                len(early_break),
                len(early_logout),
                len(break_fail),
                len(break_over_1h),
                len(short_meeting)
            ]
        }))

        # Detaylı tablolar
        with st.expander("🔍 Fail detay tabloları"):
            st.markdown("#### Geç Giriş")
            st.dataframe(pd.DataFrame(late_entry, columns=["Date", "First Available"]))

            st.markdown("#### Erken Mola")
            st.dataframe(pd.DataFrame(early_break, columns=["Date", "Break Time", "Duration (s)"]))

            st.markdown("#### Erken Çıkış")
            st.dataframe(pd.DataFrame(early_logout, columns=["Date", "Logout Time"]))

            st.markdown("#### Break > 15 dk")
            st.dataframe(pd.DataFrame(break_fail, columns=["Date", "Break Time", "Duration (s)"]))

            st.markdown("#### Günlük Break > 1 saat")
            st.dataframe(pd.DataFrame(break_over_1h, columns=["Date", "Total Break Duration (s)"]))

            st.markdown("#### Kısa Meeting/Training")
            st.dataframe(pd.DataFrame(short_meeting, columns=["Date", "Time", "Duration (s)"]))

    except Exception as e:
        st.error("🚨 An error occurred while processing the file:")
        st.exception(e)
else:
    st.info("⬆️ Please upload an Excel file to begin.")
