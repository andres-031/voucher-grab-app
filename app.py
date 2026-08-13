import datetime
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Generators Voucher Grab - Tim CIK MH",
    page_icon="🎫",
    layout="centered"
)

ADMIN_PASSWORD = "timcikmh"

# Custom Styling (CSS)
st.markdown("""
    <style>
    .stButton > button {
        border-radius: 8px;
        font-weight: bold;
    }
    .voucher-card {
        background-color: #00b14f;
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        letter-spacing: 2px;
        margin: 15px 0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }
    </style>
""", unsafe_allow_html=True)


# Inisialisasi Koneksi Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)


def get_month_sheet_name(date_obj=None):
    """Menghasilkan format nama sheet bulanan, misal: 'Agustus 2026'."""
    if date_obj is None:
        date_obj = datetime.date.today()
        
    months = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    return f"{months[date_obj.month - 1]} {date_obj.year}"


def normalize_df(df):
    """Memastikan struktur kolom sesuai."""
    required_cols = ["Kode Voucher", "Status", "Nama", "Tanggal", "Tujuan", "Waktu Klaim"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
            
    df["Status"] = df["Status"].fillna("Tersedia").replace("", "Tersedia")
    
    for col in required_cols:
        df[col] = df[col].astype(str).replace("nan", "").replace("None", "").replace("<NA>", "")
        
    return df[required_cols]


def load_database(worksheet_name):
    """Membaca data dari worksheet spesifik dengan sistem pencarian otomatis."""
    try:
        # Coba baca berdasarkan nama sheet spesifik (misal: 'Agustus 2026')
        df = conn.read(worksheet=worksheet_name, ttl=0)
        return normalize_df(df), True, worksheet_name
    except Exception:
        try:
            # Fallback otomatis ke sheet pertama jika nama sheet spesifik tidak ditemukan
            df = conn.read(worksheet=0, ttl=0)
            return normalize_df(df), True, "sheet_pertama"
        except Exception:
            empty_df = pd.DataFrame(columns=["Kode Voucher", "Status", "Nama", "Tanggal", "Tujuan", "Waktu Klaim"])
            return empty_df, False, None


def save_database(df, worksheet_name, target_sheet_type):
    """Menyimpan pembaruan data kembali ke Google Sheets."""
    if target_sheet_type == "sheet_pertama":
        conn.update(worksheet=0, data=df)
    else:
        conn.update(worksheet=worksheet_name, data=df)


# Inisialisasi Session State
if "dialog_stage" not in st.session_state:
    st.session_state.dialog_stage = None
if "claimed_voucher" not in st.session_state:
    st.session_state.claimed_voucher = ""
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False


# Dialog / Pop-up Voucher Dua Tahap
@st.dialog("🎫 Kode Voucher Grab Anda", width="large")
def render_voucher_dialog():
    if st.session_state.dialog_stage == "show_code":
        st.success("✅ **Voucher Berhasil Dialokasikan!**")
        st.write("Berikut adalah kode voucher Grab Anda:")
        
        st.markdown(
            f'<div class="voucher-card">{st.session_state.claimed_voucher}</div>',
            unsafe_allow_html=True
        )
        
        st.warning("⚠️ **PENTING:** Mohon segera **SIMPAN** atau **SCREENSHOT** kode voucher di atas sebelum menutup halaman ini!")
        
        if st.button("Selesai", type="primary", use_container_width=True):
            st.session_state.dialog_stage = "confirm_close"
            st.rerun()

    elif st.session_state.dialog_stage == "confirm_close":
        st.subheader("⚠️ Konfirmasi Penyimpanan Kode")
        st.write("Apakah Anda **pasti** sudah menyimpan atau meng-capture/screenshot kode voucher tersebut?")
        st.caption("Setelah menekan tombol **'Ya, Sudah Disimpan'**, kode tidak akan ditampilkan kembali.")
        
        col_back, col_confirm = st.columns(2)
        with col_back:
            if st.button("⬅️ Kembali (Cek Kode)", use_container_width=True):
                st.session_state.dialog_stage = "show_code"
                st.rerun()
        with col_confirm:
            if st.button("✅ Ya, Sudah Disimpan", type="primary", use_container_width=True):
                st.session_state.claimed_voucher = ""
                st.session_state.dialog_stage = None
                st.rerun()


if st.session_state.dialog_stage in ["show_code", "confirm_close"]:
    render_voucher_dialog()


# Navigation Bar
st.title("🟢 Klaim Voucher Grab Tim CIK MH")
page = st.sidebar.radio("Navigasi", ["🏠 Ambil Voucher", "🔐 Admin Panel (Database)"])


# HALAMAN 1: AMBIL VOUCHER
if page == "🏠 Ambil Voucher":
    current_month_sheet = get_month_sheet_name()
    st.subheader(f"Form Pengambilan Voucher — {current_month_sheet}")
    st.write("Silakan isi data diri dan keperluan perjalanan Anda di bawah ini:")

    with st.form(key="voucher_form", clear_on_submit=True):
        nama_input = st.text_input("1. Nama Lengkap", placeholder="Masukkan nama Anda...")
        tanggal_input = st.date_input("2. Tanggal Pemakaian", value=datetime.date.today())
        tujuan_input = st.text_input("3. Tujuan Perjalanan", placeholder="Contoh: Kantor Cabang / Kunjungan Client...")

        submit_btn = st.form_submit_button("🎟️ Ambil Voucher", type="primary", use_container_width=True)

    if submit_btn:
        if not nama_input.strip() or not tujuan_input.strip():
            st.warning("⚠️ **Mohon lengkapi Nama Lengkap dan Tujuan Perjalanan terlebih dahulu!**")
        else:
            df_db, sheet_exists, sheet_type = load_database(worksheet_name=current_month_sheet)

            if not sheet_exists or df_db.empty:
                st.error("🚨 **Mohon Maaf, Voucher Grab Belum Tersedia / Telah Habis Terpakai.**")
            else:
                available_mask = df_db["Status"].astype(str).str.strip().str.lower() == "tersedia"
                available_rows = df_db[available_mask]

                if available_rows.empty:
                    st.error("🚨 **Mohon Maaf, Voucher Grab Bulan Ini Telah Habis Terpakai.**")
                else:
                    target_idx = available_rows.index[0]
                    voucher_code = df_db.at[target_idx, "Kode Voucher"]

                    # Update ke Google Sheets
                    df_db.at[target_idx, "Nama"] = nama_input.strip()
                    df_db.at[target_idx, "Tanggal"] = tanggal_input.strftime("%Y-%m-%d")
                    df_db.at[target_idx, "Tujuan"] = tujuan_input.strip()
                    df_db.at[target_idx, "Status"] = "Terpakai"
                    df_db.at[target_idx, "Waktu Klaim"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    save_database(df_db, worksheet_name=current_month_sheet, target_sheet_type=sheet_type)

                    # Set Data Dialog
                    st.session_state.claimed_voucher = str(voucher_code)
                    st.session_state.dialog_stage = "show_code"

                    st.rerun()


# HALAMAN 2: ADMIN PANEL
elif page == "🔐 Admin Panel (Database)":
    st.subheader("Halaman Admin Database Voucher")

    if not st.session_state.admin_logged_in:
        pwd_input = st.text_input("Masukkan Password Admin:", type="password")
        if st.button("Login Admin", type="primary"):
            if pwd_input == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("Login Berhasil!")
                st.rerun()
            else:
                st.error("Password salah. Silakan coba lagi.")
    else:
        if st.sidebar.button("🔒 Logout Admin"):
            st.session_state.admin_logged_in = False
            st.rerun()

        today = datetime.date.today()
        month_options = []
        for i in range(-3, 6):
            m_date = today.replace(day=1) + datetime.timedelta(days=i*31)
            month_options.append(get_month_sheet_name(m_date))
        month_options = list(dict.fromkeys(month_options))

        selected_sheet = st.selectbox("📅 Pilih Bulan Database yang Ingin Dilihat:", month_options, index=month_options.index(get_month_sheet_name()))

        df_db, sheet_exists, sheet_type = load_database(worksheet_name=selected_sheet)

        if not sheet_exists or df_db.empty:
            st.warning(f"⚠️ Tab/Sheet dengan nama **'{selected_sheet}'** belum dibuat di Google Sheets Anda.")
        else:
            total_vouchers = len(df_db)
            used_vouchers = len(df_db[df_db["Status"].astype(str).str.strip().str.lower() == "terpakai"])
            avail_vouchers = total_vouchers - used_vouchers

            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Total Voucher", total_vouchers)
            col_m2.metric("Sisa Tersedia", avail_vouchers)
            col_m3.metric("Sudah Terpakai", used_vouchers)

            st.markdown("---")

            st.write(f"### Data Pemakaian Voucher — {selected_sheet}")
            st.dataframe(df_db, use_container_width=True)

        st.info("💡 **Status Sistem:** Terhubung ke Google Sheets. Data tersimpan permanen secara otomatis.")
