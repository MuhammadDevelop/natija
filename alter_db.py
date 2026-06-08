import sqlite3

def run():
    conn = sqlite3.connect('c:\\Users\\User\\Desktop\\gvkkfg\\natija\\markaz.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN face_encoding TEXT")
        print("Column added.")
    except Exception as e:
        print("Error:", e)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    run()
