import psycopg2
from app import config as cfg

# Подключение к первой базе данных
connection = psycopg2.connect(
    dbname="time_manager",
    user="postgres",
    password=cfg.password,
    host="localhost"
)

cursor = connection.cursor()

with open('data_export_new.csv', 'w', encoding='utf-8') as f:
    cursor.copy_expert("COPY (SELECT * FROM activities) TO STDOUT WITH CSV "
                       "HEADER", f)

# with open('data_export_new.csv', 'r', encoding='utf-8') as f:
#     cursor.copy_expert("COPY activities FROM STDIN WITH CSV HEADER", f)
# connection.commit()


cursor.close()
connection.close()
