import streamlit as st
from streamlit_option_menu import option_menu
import PIL.Image as Image
from detection import load_model, detect_disease
import pandas as pd
from db import get_detection_history 
from utils import draw_detection
import mysql.connector
import bcrypt
import logging
from mysql.connector import Error as DBError
from datetime import datetime
import io

st.set_page_config(page_title="Deteksi Daun Anggur", page_icon="🍇", layout="wide")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

#---Database connection---
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="ikabma.com",
            port=3306,
            database="ikabmaco_users_pi",
            username="ikabmaco_root",
            password="$1?q15i0Ft[OA!56"   
        )
    except DBError as e:
        logging.error(f"Error connecting to database: {e}")
        st.error(f"Database connection error: {e}")
        return None

#---User authentication---
def get_user(username):
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        # Fixed SQL query - removed password parameter
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        logging.debug(f"Retrieved user: {user}")
        return user
    except DBError as e:
        logging.error(f"Error fetching user: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Function to save detection result to database
def save_detection_result(image_data, prediction, confidence, timestamp, user_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    image_data LONGBLOB,
                    prediction VARCHAR(100),
                    confidence FLOAT,
                    timestamp DATETIME,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id VARCHAR(50)
                )
            """)
            
            # Insert detection result
            query = """
                INSERT INTO detection_history (image_data, prediction, confidence, timestamp, user_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (image_data, prediction, confidence, timestamp, user_id))
            conn.commit()
            
            return True
        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return False

# Function to save mapping owner
def save_mapping_owner(sample_id, owner_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS mapping_sample_owner (
                sample_id INT(11) PRIMARY KEY,
                owner_id VARCHAR(50) NOT NULL
            )
        """)
            
            # Insert detection result
            query = """
                INSERT INTO mapping_sample_owner (sample_id, owner_id)
                VALUES (%s, %s)
            """
            cursor.execute(query, (sample_id, owner_id))
            conn.commit()
            
            return True
        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return False

def reg_user(username, password):
    conn = get_db_connection()

    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
            
        # Create table if not exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return False
            
        # Insert new user
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        return True
        
    except DBError as e:
        logging.error(f"Error registering user: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def check_pw(hashed_password, user_password):
    logging.debug(f"Hashed password from DB: {hashed_password}")
    logging.debug(f"User password input: {user_password}")
    try:
        match = bcrypt.checkpw(user_password.encode('utf-8'), hashed_password.encode('utf-8'))
        logging.debug(f"Password match: {match}")
        return match
    except Exception as e:
        logging.error(f"Error checking password: {e}")
        return False

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'detection_results' not in st.session_state:
    st.session_state.detection_results = []


# Main app logic
if not st.session_state.logged_in:
    st.title("🍇 Deteksi Penyakit Daun Anggur")
    
    # Login/Signup menu
    menu = option_menu(
        None, 
        ["Masuk", "Daftar"], 
        icons=["box-arrow-in-right", "person-plus"],
        default_index=0, 
        orientation="horizontal"
    )

    if menu == "Masuk":
        st.subheader("Masuk ke Akun")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Masuk", type="primary"):
            if username and password:
                user = get_user(username)
                if user and check_pw(user['password'], password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Password atau Username Salah.")
            else:
                st.warning("Silahkan masukkan username dan password.")

    elif menu == "Daftar":
        st.subheader("Buat Akun Baru")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Password Confirmation", type="password")
        
        if st.button("Daftar", type="primary"):
            if new_username and new_password and confirm_password:
                if new_password != confirm_password:
                    st.error("Password do not match")
                elif len(new_password) < 6:
                    st.error("Password minimal 6 karakter!")
                elif get_user(new_username):
                    st.warning("Username already used.")
                else:
                    if reg_user(new_username, new_password):
                        st.success("Akun berhasil dibuat. Silahkan login.")
                    else:
                        st.error("Gagal membuat akun. Silahkan coba lagi.")
            else:
                st.warning("Please fill all fields.")

else:
    # Main app menu for logged in users
    st.title(f"Selamat Datang {st.session_state.username}!")
    
    selected = option_menu(
        menu_title=None,
        options=["Beranda", "Deteksi", "Riwayat", "Keluar"],
        icons=["house", "search", "folder", "box-arrow-right"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal"
    )

    if selected == "Beranda":
        st.header("Deteksi Penyakit Pada Daun Anggur")
        st.info("""
            Menggunakan teknologi YOLOv12 dengan CBAM (Convolutional Block Attention Module) 
                
            **Fitur:** 
            - 📊 Confidence scoring
            - 🏥 Informasi tentang penyakit
        """)
        
        st.write("""Anggur adalah buah kecil yang lezat, ditanam dalam kelompok, tersedia dengan banyak jenis dan warna 
            dari hijau cerah, merah tua, hitam, masing -masing dengan karakteristik rasa manis dan asam atau sedikit unik. 
            Namun, untuk memastikan kesehatan dan kualitas optimal, kesehatan anggur sangat penting. 
            Salah satu aspek terpenting adalah deteksi dini  daun anggur. Daun adalah energi "tanaman" untuk tanaman; 
            Jika daun diserang oleh penyakit ini, fotosintesisnya akan berkurang secara signifikan, 
            dan bisa mempengaruhi pertumbuhan buah, kualitas bahkan kelangsungan hidup pohon. 
            Penyakit pada daun seperti jamur, bakteri atau virus dapat menunjukkan gejala visual seperti noda, 
            perubahan warna atau deformasi. Mendeteksi dan memperbaiki masalah ini sejak awal adalah kunci untuk mencegah 
            penyebaran penyakit di semua taman dan memastikan panen anggur yang kaya dan berkualitas.""")

        # Column layout for home image display
        try:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image("images/health_leaf.jpg", caption="Daun Anggur Sehat", use_container_width=True)
            with col2:
                st.write("""
                    ### Sehat
                    Daun anggur yang sehat memiliki warna hijau cerah dan merata di seluruh permukaan daun,
                    Daun yang sehat akan tumbuh dengan ukuran yang proporsional dan bentuk yang simetris, 
                    tanpa ada distorsi, keriting, atau pengerutan yang tidak normal. Permukaan daun sehat 
                    biasanya halus, bersih, tidak kaku, rapuh, atau layu dan sedikit mengkilap. 
                    """)
            
            col3, col4 = st.columns([1, 2])
            with col3:
                st.image("images/black_rot.jpg", caption="Penyakit Black Rot", use_container_width=True)
            with col4:
                st.write("""
                    ### Penyakit Black Rot
                    Black Rot adalah penyakit jamur yang pertama kali muncul pada daun sebagai bercak-bercak kecil, 
                    yang kemudian membesar dan menjadi lebih gelap. Jamur ini berkembang pesat dalam kondisi hangat dan lembab,
                    spora jamur dapat menyebar melalui percikan air hujan atau angin. 
                    Karena dari daun inilah spora dapat menyebar ke bagian tanaman lain, terutama buah, menyebabkan kerusakan yang paling parah.
                    """)

            col5, col6 = st.columns([1, 2])
            with col5:
                st.image("images/downey_mildew.jpg", caption="Penyakit Downey Mildew", use_container_width=True)
            with col6:
                st.write("""
                ### Penyakit Downey Mildew
                Downy Mildew atau embun tepung adalah penyakit jamur yang umum dan seringkali merusak pada tanaman anggur, disebabkan oleh Plasmopara viticola. 
                Berbeda dengan Black Rot yang cenderung membuat daun mengering, Downy Mildew lebih suka lingkungan yang lembab dan dingin. 
                Penyakit ini dapat dengan cepat menyebar melalui spora yang terbawa angin atau percikan air hujan, menyerang semua bagian hijau tanaman, 
                terutama daun dan buah muda. Kerusakan pada daun dapat secara signifikan mengurangi kemampuan fotosintesis tanaman, 
                yang berdampak pada kualitas dan kuantitas hasil panen.
                """)
        except FileNotFoundError:
            st.warning("⚠️ Gambar tidak ditemukan. Pastikan folder 'images' dan file gambar tersedia.")

    elif selected == "Deteksi":
        st.header("🔍 Deteksi Penyakit Daun Anggur")

        # Load model
        try:
            model = load_model()
            if model is None:
                st.warning("⚠️ Model YOLOv12 tidak ditemukan. Menggunakan mode simulasi untuk demo.")
        except Exception as e:
            st.error(f"Error loading model: {e}")
            model = None

        # Image upload
        uploaded_file = st.file_uploader(
            "📸 Unggah Gambar Daun Anggur Di Bawah Sini",
            type=['jpg', 'jpeg', 'png'],
            help="Unggah Gambar Daun Anggur Di Bawah Sini"
        )
        image_source = uploaded_file
        
        # Load and display image
        if image_source is not None:
            try:
        # Konversi hasil kamera atau upload menjadi gambar RGB
                image = Image.open(image_source).convert("RGB")
                col1, col2 = st.columns(2)
        
                with col1:
                    st.subheader("Gambar Asli")
                    st.image(image, use_container_width=True)

        # Detection button
                if st.button("Mulai Deteksi", type="primary", use_container_width=True):
                    with st.spinner("Sedang menganalisis gambar..."):
                        try:
                            detection_result = detect_disease(image, model)

                            if detection_result:
                                result_image = draw_detection(detection_result['results'])

                                with col2:
                                    st.subheader("Hasil Deteksi")
                                    st.image(result_image, use_container_width=True)
                                    st.write(f"**Prediction:** {detection_result.get('prediction', 'Unknown')}")
                                    st.write(f"**Confidence:** {detection_result.get('confidence', 0):.2f}%")
                                    #st.write(f"**Timestamp:** {datetime.now()}")
                                    #st.write(f"**Disease Name:** {detection_result.get('prediction', 'Unknown')}")
                                    #st.write(f"**Class:** {detection_result.get('class', 'Unknown')}")
                                    

                                    new_result = {
                                        'timestamp': datetime.now(),
                                        'disease_name': detection_result.get('prediction', 'Unknown'),
                                        'confidence': detection_result.get('confidence', 0),
                                        'class': detection_result.get('class', 'Unknown') # Pastikan 'class' juga disimpan
                                    }

                                    st.session_state.detection_results.append(new_result)
                                    st.success("Hasil deteksi berhasil disimpan di sesi ini.")
                                    
                                # Save to database
                                    try:
                                        img_byte_arr = io.BytesIO()
                                        image.save(img_byte_arr, format='PNG')
                                        img_byte_arr = img_byte_arr.getvalue()

                                        is_saved = save_detection_result(
                                            img_byte_arr,
                                            detection_result.get('prediction', 'Unknown'),
                                            detection_result.get('confidence', 0),
                                            datetime.now(),
                                            st.session_state.username
                                        )

                                        if is_saved:
                                            st.success("Hasil deteksi berhasil disimpan ke database!")
                                        else:
                                            st.error("Gagal menyimpan hasil ke database. Cek koneksi dan konfigurasi.")
                                    except Exception as e:
                                        st.warning(f"Could not save to database: {e}")
                            else:
                                st.error("Failed to detect disease. Please try again.")
                        except Exception as e:
                            st.error(f"Error during detection: {e}")
            except Exception as e:
                st.error(f"Error loading image: {e}")
        else:
            st.info("Silakan unggah gambar atau ambil foto untuk memulai deteksi.")


    elif selected == "Riwayat":
        st.header("📊 Riwayat Deteksi")
        
        # Get history from database
        try:
            db_history = get_detection_history()
        except Exception as e:
            st.warning(f"Could not load database history: {e}")
            db_history = []
        
        # Session state history
        session_results = st.session_state.detection_results
        
        if not session_results and not db_history:
            st.info("Belum ada riwayat deteksi. Mulai deteksi untuk melihat riwayat di sini.")
        else:
            # Statistics section
            st.subheader("📈 Statistik Sesi Saat Ini")
            
            if session_results:
                # Analysis from session state
                df_results = pd.DataFrame([
                    {
                        'Timestamp': r['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                        'Disease': r['disease_name'],
                        'Confidence': f"{r['confidence']:.2f}%",
                        'Status': 'Sehat' if r['class'] == 'healthy' else 'Sakit'
                    }
                    for r in session_results
                ])
                st.dataframe(df_results, use_container_width=True)
            else:
                st.info("Tidak ada hasil deteksi dalam sesi ini.")

            # Database history table
            if db_history:
                st.subheader("💾 Riwayat Database")
                try:
                    db_df = pd.DataFrame(db_history, columns=['ID', 'Prediction', 'Confidence', 'Timestamp', 'Created At'])
                    st.dataframe(db_df, use_container_width=True)
                except Exception as e:
                    st.error(f"Error displaying database history: {e}")
            else:
                st.info("Tidak ada riwayat dalam database.")

    elif selected == "Keluar":
        st.header("👋 Keluar")
        if st.button("Konfirmasi Keluar", type="primary"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.detection_results = []
            st.success("Berhasil Keluar Dari Aplikasi!")
            st.rerun()
        else:
            st.info("Klik tombol di atas untuk keluar.")
