import sqlite3
from datetime import datetime, timedelta, UTC

con = sqlite3.connect("./database/person.db")
cur = con.cursor()

def clear_db():
    now = (datetime.now(UTC) + timedelta(hours=3)).isoformat()
    
    # Удаляем записи, где end_time меньше now
    cur.execute("DELETE FROM key WHERE end_time < ?", (now,))
    con.commit()

    # Проверяем количество оставшихся записей
    res = cur.execute("SELECT COUNT(*) FROM key")
    print(res.fetchone()[0])  # Выводим количество строк в таблице

clear_db()
