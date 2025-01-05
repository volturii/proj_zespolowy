import sqlite3
from flask import Flask, render_template, request
import re
from datetime import datetime, timedelta

app = Flask(__name__)

# Funkcja do połączenia z bazą danych
def polaczenie_z_baza():
    return sqlite3.connect('logs_database.db')

# Funkcja do normalizacji dat
def normalize_date(log_date):
    pattern = r'(\d{2})/(\w{3})/(\d{4}):(\d{2}):(\d{2}):(\d{2})'
    months = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05",
        "Jun": "06", "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10",
        "Nov": "11", "Dec": "12"
    }
    match = re.match(pattern, log_date)
    if match:
        day, month_str, year, hour, minute, second = match.groups()
        return f"{year}-{months.get(month_str, '01')}-{day} {hour}:{minute}:{second}"
    return None

# Funkcja do pobierania logów z bazy i ich filtrowania
def get_filtered_logs(start_date, end_date, tabela):
    if not re.match(r'^[a-zA-Z0-9_]+$', tabela):  # Walidacja nazwy tabeli
        raise ValueError("Nieprawidłowa nazwa tabeli.")
    
    query = f"SELECT date_time FROM {tabela}"
    with polaczenie_z_baza() as con:
        cursor = con.cursor()
        rows = cursor.execute(query).fetchall()

    return [
        normalize_date(row[0]) for row in rows
        if normalize_date(row[0]) and start_date <= normalize_date(row[0])[:10] <= end_date
    ]

# Funkcja do obliczenia zakresu dat
def get_date_range(period):
    today = datetime.now()
    if period == "popTydzien":
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
    elif period == "aktTydzien":
        start = today - timedelta(days=today.weekday())
        end = today
    elif period == "dzisiaj":
        start = end = today
    else:
        return None, None
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

# Funkcja do grupowania logów
def group_logs(filtered_logs, start_date, end_date, group_by="day"):
    log_counts = {}
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Uwzględnij koniec dnia

    if group_by == "day":
        current_date = start_datetime
        while current_date < end_datetime:
            log_counts[current_date.strftime('%Y-%m-%d')] = 0
            current_date += timedelta(days=1)
        for log in filtered_logs:
            date = log[:10]
            if date in log_counts:
                log_counts[date] += 1

    elif group_by == "hour" and len(set(log[:10] for log in filtered_logs)) == 1:
        log_counts = {f"{hour:02d}:00": 0 for hour in range(24)}  # Dodano ":00" do formatu godzin
        for log in filtered_logs:
            hour = log[11:13] + ":00"  # Dodano ":00" do zapisu godzin
            log_counts[hour] += 1


    elif group_by == "4hour":
        current_datetime = start_datetime
        while current_datetime < end_datetime:
            key = current_datetime.strftime('%Y-%m-%d %H:%M')
            log_counts[key] = 0
            current_datetime += timedelta(hours=4)
        for log in filtered_logs:
            log_time = datetime.strptime(log, '%Y-%m-%d %H:%M:%S')
            for interval_start in log_counts.keys():
                interval_start_dt = datetime.strptime(interval_start, '%Y-%m-%d %H:%M')
                if interval_start_dt <= log_time < interval_start_dt + timedelta(hours=4):
                    log_counts[interval_start] += 1
                    break

    return sorted(log_counts.keys()), [log_counts[key] for key in sorted(log_counts.keys())]

# Strona główna
@app.route("/")
def home():
    return render_template("index.html")

# Wyświetlenie wykresu dla predefiniowanego okresu czasu
@app.route("/wykresPoloczen/<okresCzasu>")
def wykresPoloczenZakres(okresCzasu):
    tabela = request.args.get("tabela", "nginx_logs")
    start_date, end_date = get_date_range(okresCzasu)
    if not start_date or not end_date:
        return "Nieprawidłowy okres czasu", 400

    filtered_logs = get_filtered_logs(start_date, end_date, tabela)
    delta = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days

    if delta == 0:
        group_by = "hour"  # Używaj godzin tylko dla pojedynczego dnia
    elif delta == 1:
        group_by = "4hour"  # Używaj odstępów co 4 godziny dla dwóch dni
    else:
        group_by = "day"  # Standardowe grupowanie dzienne

    dates, counts = group_logs(filtered_logs, start_date, end_date, group_by)

    if delta == 0:
        dates = [date for date in dates]  # Usuwanie daty, pozostawienie tylko godzin

    okresCzasuWykresu = {
        "popTydzien": f"Wykres z tabeli {tabela}: Poprzedni tydzień (poniedziałek-niedziela)",
        "aktTydzien": f"Wykres z tabeli {tabela}: Bieżący tydzień (poniedziałek-dzisiaj)",
        "dzisiaj": f"Wykres z tabeli {tabela}: Dzisiaj"
    }.get(okresCzasu, "Wykres")

    return render_template('wykresPoloczen.html', dates=dates, counts=counts, okresCzasuWykresu=okresCzasuWykresu)

# Wyświetlenie wykresu dla zakresu dat podanego przez użytkownika
@app.route('/wykresPoloczen', methods=['GET'])
def search():
    tabela = request.args.get('tabela', 'nginx_logs')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if not start_date or not end_date:
        return "Musisz podać zakres dat", 400

    filtered_logs = get_filtered_logs(start_date, end_date, tabela)
    delta = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days

    if delta == 0:
        group_by = "hour"  # Używaj godzin tylko dla pojedynczego dnia
    elif delta == 1:
        group_by = "4hour"  # Używaj odstępów co 4 godziny dla dwóch dni
    else:
        group_by = "day"  # Standardowe grupowanie dzienne

    dates, counts = group_logs(filtered_logs, start_date, end_date, group_by)

    if delta == 0:
        dates = [date for date in dates]  # Usuwanie daty, pozostawienie tylko godzin

    okresCzasuWykresu = f"Wykres z tabeli {tabela}: {start_date} - {end_date}"
    return render_template('wykresPoloczen.html', dates=dates, counts=counts, okresCzasuWykresu=okresCzasuWykresu)

if __name__ == "__main__":
    app.run(debug=True)
