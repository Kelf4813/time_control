import time
from datetime import datetime, timedelta

import psycopg2

from app import config as cfg
from app import modules as md

connection = psycopg2.connect(
    dbname="time_manager",
    user="postgres",
    password=cfg.password,
    host="localhost"
)
connection.autocommit = True

with connection.cursor() as cursor:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id serial PRIMARY KEY,
        user_id BIGINT,
        created_time BIGINT,
        region INT,
        start_time INT
    )
    ''')
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS activities(
            id serial PRIMARY KEY,
            user_id BIGINT,
            rate INT,
            description TEXT,
            time BIGINT,
            date TEXT
        );"""
    )


def add_user(user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """INSERT INTO users (user_id, created_time, region, start_time) 
            VALUES (%s, %s, %s, %s)""",
            (user_id, int(time.time()), 0, 8)
        )


def get_user_info(user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT created_time, region, start_time
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        return cursor.fetchone()


def get_user_time_zone(user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT region
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        return cursor.fetchone()


def avg_all_time(user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT AVG(rate)
            FROM activities
            WHERE user_id = %s
        """, (user_id,))
        return round(float(cursor.fetchone()[0]), 2)


def check_user(user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT user_id
                FROM users """)
        users = cursor.fetchall()
        if ((user_id),) not in users:
            return True
        else:
            return False


def add_data(data):
    with connection.cursor() as cursor:
        cursor.execute(
            """INSERT INTO activities (user_id, rate, time, description,
            date) VALUES (%s, %s, %s, %s, %s)""",
            (data['user_id'], data['rate'], int(data['time']), data[
                'description'].capitalize(), data['date'])
        )


def check_date(user_id, date):
    with connection.cursor() as cursor:
        cursor.execute('''
        SELECT date
        FROM activities
        WHERE user_id=%s;''',
                       (user_id,))
        column_data = cursor.fetchall()
        return (date,) in column_data


def data_date(user_id, days=0):
    target_date = datetime.now() - timedelta(days=days)
    with connection.cursor() as cursor:
        cursor.execute("""
          SELECT rate, time, description
            FROM activities
            WHERE to_timestamp(time) >= date_trunc('day', %s)
              AND to_timestamp(time) < date_trunc('day', %s + INTERVAL '1 day')
              AND user_id = %s;
        """, (target_date, target_date, user_id))
        column_data = cursor.fetchall()
        sorted_data = sorted(column_data, key=lambda x: x[1])
        timestamp_dict = {timestamp: {'rate': rate, 'description': description}
                          for rate, timestamp, description in sorted_data}
        return timestamp_dict


def data_to_draw(user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT rate, time
         FROM activities
         WHERE user_id = %s;""",
                       (user_id,))
        column_data = cursor.fetchall()
        return column_data


def data_today(user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT rate, description, time
            FROM activities
            WHERE to_timestamp(time) >= date_trunc('day', NOW())
            AND user_id = %s;
        """, (user_id,))
        column_data = cursor.fetchall()
        sorted_data = sorted(column_data, key=lambda x: x[2])
        timestamp_dict = {timestamp: {'rate': rate, 'description': description}
                          for rate, description, timestamp in sorted_data}
        return timestamp_dict


def data_30d(user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DATE(to_timestamp(time)) AS day,
                   AVG(rate) AS count_records
            FROM activities
            WHERE to_timestamp(time) >= NOW() - INTERVAL '30 days'
              AND user_id = %s
            GROUP BY DATE(to_timestamp(time))
            ORDER BY day;
        """, (user_id,))
        column_data = cursor.fetchall()
        result = {}
        for i in column_data:
            result[i[0].strftime("%d.%m")] = round(float(i[1]), 2)
        return result


def all_users():
    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT user_id
        FROM users
        """)
        return cursor.fetchall()


def get_distribution_user(user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT start_time, region
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        data = cursor.fetchone()
        region = data[1]
        hours = md.generate_hours(data[0])
        if datetime.now().hour + region in hours:
            return user_id


if __name__ == '__main__':
    print(get_distribution_user(1098640843))
    pass
