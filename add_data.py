import sqlite3

# Połącz z bazą danych
conn = sqlite3.connect('logs_databaseip.db')
cursor = conn.cursor()

# Lista danych do dodania: (date_time, ip, method)
log_entries = [
    ("17/Dec/2024:02:03:23 +0000", "20.168.0.1", "POST"),
    ("17/Dec/2024:02:05:45 +0000", "20.168.0.1", "GET"),
    ("17/Dec/2024:02:06:12 +0000", "20.168.0.1", "PUT"),
    ("17/Dec/2024:02:03:23 +0000", "20.168.0.1", "POST"),
    ("17/Dec/2024:02:05:45 +0000", "20.168.0.1", "GET"),
    ("17/Dec/2024:02:06:12 +0000", "20.168.0.1", "PUT"),
    ("17/Dec/2024:02:03:23 +0000", "20.168.0.1", "POST"),
    ("17/Dec/2024:02:05:45 +0000", "20.168.0.1", "GET"),
    ("17/Dec/2024:02:06:12 +0000", "20.168.0.1", "PUT"),
    ("17/Dec/2024:02:03:23 +0000", "10.168.0.1", "POST"),
    ("17/Dec/2024:02:05:45 +0000", "10.168.0.1", "GET"),
    ("17/Dec/2024:02:06:12 +0000", "10.168.0.1", "PUT")
]

# Wstawianie danych do bazy danych
for entry in log_entries:
    cursor.execute("""
        INSERT INTO nginx_logs (date_time, ip, method) 
        VALUES (?, ?, ?)
    """, entry)

# Zatwierdzenie zmian i zamknięcie połączenia
conn.commit()
conn.close()

print("Logi zostały dodane do bazy danych.")
