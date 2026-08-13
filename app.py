import os
import datetime
import pandas as pd
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Generators Voucher Grab - Tim CIK MH",
    page_icon="🎫",
    layout="centered"
)

# Definisi Konstanta
EXCEL_FILE = "Voucher Grab Tim CMH.xlsx"
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


def normalize_df(df):
    """Memastikan struktur kolom Excel sesuai dan bertipe data string."""
    column_mapping = {
        'kode': 'Kode Voucher',
        'voucher': 'Kode Voucher',
        'status': 'Status',
        'nama': 'Nama',
        'tanggal': 'Tanggal',
        'tujuan': 'Tujuan'
    }
    
    df.columns = [column_mapping.get(str(col).lower().strip(), col) for col in df.columns]

    required_cols = ["Kode Voucher", "Status", "Nama", "Tanggal", "Tujuan", "Waktu Klaim"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
            
    df["Status"] = df["Status"].fillna("Tersedia").replace("", "Tersedia")
    
    for col in required_cols:
        df[col] = df[col].astype(str).replace("nan", "").replace("None", "")
        
    return df[required_cols]


def load_database():
    """Membaca file database Excel lokal."""
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            return normalize_df(df)
        except Exception:
            pass

    sample_data = {
        "Kode Voucher": [f"GRAB-CMH-{i:03d}" for i in range(1, 11)],
        "Status": ["Tersedia"] * 10,
        "Nama": [""] * 10,
        "Tanggal": [""] * 10,
        "Tujuan": [""] * 10,
        "Waktu Klaim": [""] * 10
    }
    df = pd.DataFrame(sample_data)
    df.to_excel(EXCEL_FILE, index=False)
    return df


def save_database(df):
    """Menyimpan dataframe kembali ke file Excel."""
    df.to_excel(EXCEL_FILE, index=False)


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
    st.subheader("Form Pengambilan Voucher")
    st.write("Silakan isi data diri dan keperluan perjalanan Anda di bawah ini:")

    # Penggunaan st.form dengan clear_on_submit=True untuk MERESET otomatis input saat diklik
    with st.form(key="voucher_form", clear_on_submit=True):
        nama_input = st.text_input("1. Nama Lengkap", placeholder="Masukkan nama Anda...")
        tanggal_input = st.date_input("2. Tanggal Pemakaian", value=datetime.date.today())
        tujuan_input = st.text_input("3. Tujuan Perjalanan", placeholder="Contoh: Kantor Cabang / Kunjungan Client...")

        submit_btn = st.form_submit_button("🎟️ Ambil Voucher", type="primary", use_container_width=True)

    if submit_btn:
        # Validasi Form
        if not nama_input.strip() or not tujuan_input.strip():
            st.warning("⚠️ **Mohon lengkapi Nama Lengkap dan Tujuan Perjalanan terlebih dahulu!**")
        else:
            df_db = load_database()

            available_mask = df_db["Status"].astype(str).str.strip().str.lower() == "tersedia"
            available_rows = df_db[available_mask]

            if available_rows.empty:
                st.error("🚨 **Mohon Maaf, Voucher Grab Bulan Ini Telah Habis Terpakai.**")
            else:
                target_idx = available_rows.index[0]
                voucher_code = df_db.at[target_idx, "Kode Voucher"]

                # Update Database
                df_db.at[target_idx, "Nama"] = nama_input.strip()
                df_db.at[target_idx, "Tanggal"] = tanggal_input.strftime("%Y-%m-%d")
                df_db.at[target_idx, "Tujuan"] = tujuan_input.strip()
                df_db.at[target_idx, "Status"] = "Terpakai"
                df_db.at[target_idx, "Waktu Klaim"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                save_database(df_db)

                # Panggil Pop-up Dialog
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

        df_db = load_database()

        total_vouchers = len(df_db)
        used_vouchers = len(df_db[df_db["Status"].astype(str).str.strip().str.lower() == "terpakai"])
        avail_vouchers = total_vouchers - used_vouchers

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Voucher", total_vouchers)
        col_m2.metric("Sisa Tersedia", avail_vouchers)
        col_m3.metric("Sudah Terpakai", used_vouchers)

        st.markdown("---")

        tab_view, tab_upload = st.tabs(["📊 Lihat Database", "📤 Upload Excel Baru"])

        with tab_view:
            st.write("### Data Pemakaian Voucher")
            st.dataframe(df_db, use_container_width=True)

            with open(EXCEL_FILE, "rb") as f:
                st.download_button(
                    label="📥 Download Database Excel Ter-update",
                    data=f,
                    file_name=f"Voucher_Grab_CMH_Update_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        with tab_upload:
            st.write("### Upload Database Voucher Bulanan")
            st.info("Unggah file Excel baru setiap awal bulan. File harus memiliki kolom utama **Kode Voucher**.")

            uploaded_file = st.file_uploader("Pilih file Excel (.xlsx / .xls)", type=["xlsx", "xls"])
            if uploaded_file is not None:
                try:
                    new_df = pd.read_excel(uploaded_file)
                    normalized_new_df = normalize_df(new_df)

                    st.write("Preview Data Baru:")
                    st.dataframe(normalized_new_df, use_container_width=True)

                    if st.button("⚠️ Gantikan Database Sekarang", type="primary"):
                        save_database(normalized_new_df)
                        st.success("Database Excel berhasil diperbarui dengan data baru!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Gagal membaca file Excel: {e}")
