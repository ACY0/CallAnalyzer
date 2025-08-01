import streamlit as st
import pandas as pd

st.set_page_config(page_title="Call Center Analyzer", layout="wide")

st.title("📊 Call Center Log Analyzer")
st.write("Yüklediğiniz Excel dosyasındaki günlük sistem loglarını analiz eder.")

# 1. Dosya Yükleme
uploaded_file = st.file_uploader("Excel dosyanızı yükleyin (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0)

        # 🧠 Sütun başlıklarını temizle (boşluk, tab, enter varsa kırar)
        df.columns = df.columns.str.strip()
        st.success("✅ Dosya başarıyla yüklendi.")

        # 👁 Sütun başlıklarını göster (debug amaçlı)
        st.write("📌 Sütun Başlıkları:", df.columns.tolist())

        # Örnek analiz: İlk 'Available' zamanı
        df["Date"] = pd.to_datetime(df["Date"])
        df_sorted = df.sort_values(by=["Date", "Start time"], ascending=[True, True])

        # Her gün için ilk Available zamanı
        results = []
        for date, group in df_sorted.groupby(df_sorted["Date"].dt.date):
            available_rows = group[group["State"] == "Available"]
            if not available_rows.empty:
                first_avail_time = pd.to_datetime(available_rows.iloc[0]["Start time"]).time()
                results.append({"Date": date, "First Available": first_avail_time})

        result_df = pd.DataFrame(results)

        st.subheader("📅 İlk Available Saatleri (Günlük Bazda)")
        st.dataframe(result_df)

    except Exception as e:
        st.error("🚨 Dosya okunurken bir hata oluştu:")
        st.exception(e)
else:
    st.info("⬆️ Lütfen bir Excel dosyası yükleyin.")
