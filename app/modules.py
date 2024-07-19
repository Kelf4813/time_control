import time
from datetime import datetime

collors = [
    '#35B400',
    '#FF4939',
    '#000000'
]


def get_entries_by_date(day_month, data):
    try:
        input_date = datetime.strptime(day_month, '%d:%m')
    except ValueError:
        return None
    results = {}

    for row in data:
        timestamp = row[3]
        row_date = datetime.fromtimestamp(timestamp)

        if (row_date.day == input_date.day and row_date.month ==
                input_date.month):
            results[row[3]] = {
                'rate': row[1],
                'description': row[2]
            }

    return results


def str_to_time(date_string, time_zone):
    try:
        if ':' in date_string:
            parts = date_string.split(':')
        for i in parts:
            if not i.isdigit() or i == '0':
                return None
        if len(parts) == 3:
            hours = int(parts[0]) + int(parts[1]) * 24 + time_zone
            hour = hours % 24
            day = hours // 24
            month = int(parts[2])
            current_year = time.localtime().tm_year
            given_time = time.struct_time(
                (current_year, month, day, hour, 0, 0, 0, 0, -1))
        elif len(parts) == 2:
            day = int(parts[0])
            month = int(parts[1])
            current_year = time.localtime().tm_year
            given_time = time.struct_time(
                (current_year, month, day, 0, 0, 0, 0, 0, -1))
        seconds_since_epoch = time.mktime(given_time)
        return seconds_since_epoch
    except Exception as ex:
        print(ex)


def time_to_date(seconds_since_epoch):
    try:
        dt_object = datetime.fromtimestamp(seconds_since_epoch)
        date_string = dt_object.strftime("%H:%d:%m")
        return date_string
    except ValueError:
        print("Ошибка: Неверное количество секунд с начала отсчета")
        return None


def statistics_mes(data):
    mes = ''
    for i in data:
        hour = str(time.localtime(i).tm_hour - 1)
        if len(hour) == 1:
            hour = f'0{hour}:00'
        else:
            hour = f'{hour}:00'
        mes += f'{hour} - {data[i]["description"]}\n'
    return mes[:-1]


def calculate_percentage(number1, number2):
    percentage_difference = ((number1 - number2) / number2) * 100

    if percentage_difference > 0:
        return f"+{percentage_difference:.2f}%", collors[0]
    elif percentage_difference < 0:
        return f"{percentage_difference:.2f}%", collors[1]
    else:
        return "0%", collors[2]


def generate_hours(start_hour):
    if -1 < start_hour < 25:
        result = []
        current_hour = start_hour

        for _ in range(16):
            current_hour = (current_hour) % 24
            result.append(current_hour)
            current_hour += 1
        return result


if __name__ == '__main__':
    for i in range(24):
        print(i, generate_hours(i))
