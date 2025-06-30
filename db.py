import mysql.connector
import streamlit as st
import hashlib


#---Function to hash passwords---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

#---Connect to the database---
try:
    mydb = mysql.connector.connect(
        host="ikabma.com",          # Gunakan = dan tanda kutip
        port=3306,                 # port adalah parameter terpisah dan berupa angka (integer)
        database="ikabmaco_users_pi", # Gunakan = dan tanda kutip
        user="ikabmaco_root",       # Parameter yang benar adalah 'user', bukan 'username'
        password="$1?q15i0Ft[OA!56"  # Gunakan = dan tanda kutip
    )
except mysql.connector.Error as err:
    st.error(f"Error: {err}")
    st.stop()

# Database connection
def get_db_connection():
    conn = mysql.connector.connect(
        host: ikabma.com port : 3306,
        database : ikabmaco_users_pi,
        username: ikabmaco_root,
        password: $1?q15i0Ft[OA!56   
    )
    return conn

# Function to save detection result to database
def save_detection_result(image_data, prediction, confidence, timestamp):
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
# Insert detection result
            query = """
                INSERT INTO detection_history (image_data, prediction, confidence, timestamp)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (image_data, prediction, confidence, timestamp))
            conn.commit()
            
            cursor.close()
            conn.close()
            return True
        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")
            return False
    return False

# Function to get detection history from database
def get_detection_history():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, prediction, confidence, timestamp, created_at 
                FROM detection_history 
                ORDER BY created_at DESC 
                LIMIT 50
            """)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")
            return []
    #return []


def masuk():
    st.title("Login")
    u = st.text_input("Username", key="login_username")
    p = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        if u and p:
            hashed_password = hash_password(p)
            try:
                mycursor = mydb.cursor()
                mycursor.execute("SELECT * FROM user WHERE username = %s AND password = %s", (u, hashed_password))
                user = mycursor.fetchone()
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = u
                    st.success("Login successful!")
                    st.experimental_rerun()  # Refresh app untuk menampilkan home page
                else:
                    st.error("Invalid username or password.")
            except mysql.connector.Error as err:
                st.error(f"Error: {err}")
            finally:
                mycursor.close()
        else:
            st.warning("Please enter both username and password.")


