from datetime import datetime, timedelta
import time

from PIL import Image, ImageDraw, ImageFont

from app import database as db
from app import modules as md


class DrawStatistic:
    def __init__(self, time_zone):
        self.time_zone = time_zone

    def get_time(self):
        return time.time() + self.time_zone * 3600

    def get_datetime(self):
        if self.time_zone < 0:
            return datetime.now() - timedelta(hours=self.time_zone)
        else:
            return datetime.now() + timedelta(hours=self.time_zone)

    def is_this_week(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        current_week_start = self.get_datetime() - timedelta(
            days=self.get_datetime().weekday())
        current_week_start = current_week_start.replace(hour=0, minute=0,
                                                        second=0,
                                                        microsecond=0)
        return dt >= current_week_start

    def is_yesterday(self, timestamp):
        now = self.get_datetime()
        yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0,
                                                            second=0,
                                                            microsecond=0)
        yesterday_end = (now - timedelta(days=1)).replace(hour=23, minute=59,
                                                          second=59,
                                                          microsecond=999999)
        date = datetime.fromtimestamp(timestamp)
        return yesterday_start <= date <= yesterday_end

    def get_text_width(self, text, font):
        dummy_image = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_image)
        bbox = draw.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        return width

    def get_color(self, points):
        if 1 <= points <= 2:
            return "#FF4939"
        elif 2 <= points <= 4:
            return "#F9CB9C"
        elif 4 <= points <= 6:
            return "#D5A6BD"
        elif 6 <= points <= 8:
            return "#9FC5E8"
        elif 8 <= points <= 10:
            return "#B6D7A8"

    def draw_info(self, data_db, draw_info, image, day_month, user_id):
        dates_this_week = [(value, timestamp) for value, timestamp in data_db
                           if self.is_this_week(timestamp)]
        dates_yesterday = [(value, timestamp) for value, timestamp in data_db
                           if self.is_yesterday(timestamp)]
        all_rate = []
        today_rate = []
        week_rate = []
        yesterday_rate = []
        for i in data_db:
            all_rate.append(i[0])
        for i in draw_info:
            today_rate.append(draw_info[i]['rate'])
        for i in dates_this_week:
            week_rate.append(i[0])
        for i in dates_yesterday:
            yesterday_rate.append(i[0])

        if all_rate and today_rate and week_rate:
            all_avg = round(sum(all_rate) / len(all_rate), 2)
            today_avg = round(sum(today_rate) / len(today_rate), 2)
            week_avg = round(sum(week_rate) / len(week_rate), 2)
            if yesterday_rate:
                yesterday_avg = round(
                    sum(yesterday_rate) / len(yesterday_rate), 2)
                all_minis_today = round((sum(all_rate) - sum(today_rate)) / (
                        len(all_rate) - len(today_rate)), 2)
            else:
                yesterday_avg = 0
                all_minis_today = 0
            if today_rate != week_rate:
                week_minis_today = round((sum(week_rate) - sum(today_rate)) / (
                        len(week_rate) - len(today_rate)), 2)
            else:
                week_minis_today = today_avg
            if yesterday_avg:
                percent_today = md.calculate_percentage(today_avg,
                                                        yesterday_avg)
                percent_week = md.calculate_percentage(today_avg,
                                                       week_minis_today)
                percent_all = md.calculate_percentage(all_avg, all_minis_today)
            else:
                percent_today = (0, 'black')
                percent_week = (0, 'black')
                percent_all = (0, 'black')
            font_size = 40
            font = ImageFont.truetype("font.ttf", font_size)
            if ':' in day_month:
                input_date = datetime.strptime(day_month, '%d:%m')
                formatted_date = input_date.strftime('%d.%m') + '.24'
            else:
                formatted_date = day_month + '.24'
            draw = ImageDraw.Draw(image)

            width_all = self.get_text_width(f"{all_avg} /", font)
            width_week = self.get_text_width(f"{week_avg} /", font)
            width_today = self.get_text_width(f"{today_avg} /", font)

            draw.text((411, 95), f"{all_avg} /", font=font, fill='black')
            draw.text((448, 181), f"{week_avg} / ", font=font, fill='black')
            draw.text((413, 267), f"{today_avg} / ", font=font, fill='black')

            draw.text((width_all + 411 + 9, 95), f"{percent_all[0]}",
                      font=font,
                      fill=percent_all[1])
            draw.text((width_week + 448 + 9, 181), f"{percent_week[0]}",
                      font=font,
                      fill=percent_week[1])
            draw.text((width_today + 413 + 9, 267), f"{percent_today[0]}",
                      font=font, fill=percent_today[1])

            draw.text((1478, 95), formatted_date, font=font, fill='black')
            image.save(f'img/{user_id}_day.png')

    def draw_new_post(self, x, x2, y, image, rate):
        draw = ImageDraw.Draw(image)
        color = self.get_color(rate)
        draw.rounded_rectangle(
            [(x, y), (x2, y + round(50 * rate))],
            outline='black',
            fill=color,
            width=1,
            radius=5
        )
        return image

    def draw_info_30(self, info, image, user_id):
        font = ImageFont.truetype("font.ttf", 40)
        draw = ImageDraw.Draw(image)
        min_key = min(info, key=info.get)
        max_key = max(info, key=info.get)
        avg = str(db.avg_all_time(user_id))
        width_all = self.get_text_width(f"{max_key} /", font)
        draw.text((276, 95), f"{max_key} /", font=font, fill='black')
        draw.text((width_all + 276 + 9, 95), f"{info[max_key]}", font=font,
                  fill='black')
        draw.text((315, 181), f"{min_key} /", font=font, fill='black')
        draw.text((width_all + 315 + 9, 181), f"{info[min_key]}", font=font,
                  fill='black')
        draw.text((352, 267), avg, font=font, fill='black')
        return image

    def draw_30d(self, user_id):
        last_30_days = db.data_30d(user_id)
        if last_30_days:
            font_size = 29
            image = Image.open('img/background_30.png').convert("RGBA")
            font = ImageFont.truetype("font.ttf", font_size)
            main_image_x, main_image_y = 56, 935
            post_x = 105
            post_y = 882
            for date in last_30_days:
                rate = last_30_days[date]
                text_image = Image.new('RGBA', (82, 35), (255, 255, 255, 0))
                draw = ImageDraw.Draw(text_image)
                x = 83 - self.get_text_width(date, font)
                draw.text((x, 0), date, font=font, fill='black')
                rotated_text_image = text_image.rotate(45, expand=1,
                                                       resample=Image.BICUBIC)
                image.paste(rotated_text_image, (main_image_x, main_image_y),
                            rotated_text_image)
                image = self.draw_new_post(post_x, post_x + 29,
                                           post_y - round(50 * (rate - 1)),
                                           image,
                                           rate)
                main_image_x += 53
                post_x += 53
            draw = ImageDraw.Draw(image)
            draw.line((90, 930, 1700, 930), fill='black', width=2)
            image = self.draw_info_30(last_30_days, image, user_id)
            image.save(f'img/{user_id}_month.png')

    def draw_time(self, start_hour):
        hours = md.generate_hours(start_hour)
        if hours:
            image = Image.open('img/back_test.png'
                               '').convert("RGBA")
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype("font.ttf", 29)

            x = 82
            y = 948
            for hour in hours:
                if len(str(hour)) == 1:
                    hour = f"0{hour}:00"
                else:
                    hour = f"{hour}:00"
                draw.text((x, y), hour, font=font, fill='black')
                x += 100
            return image

    def draw_day(self, day_month, user_id):
        try:
            data_db = db.data_to_draw(user_id)
            data_user = db.get_user_info(user_id)
            start_hour = data_user[2]
            days = int((self.get_time() -
                        md.str_to_time(day_month, self.time_zone)) / 86400)
            data_draw = db.data_date(user_id, days)
            image = self.draw_time(start_hour)
            for i in data_draw:
                hour = time.localtime(i).tm_hour - start_hour
                rate = data_draw[i]['rate']
                x = 100 * hour
                y = 883 - 50 * (rate - 1)
                image = self.draw_new_post(x, x + 50, y - 1, image, rate)
                draw = ImageDraw.Draw(image)
                draw.line((90, 930, 1700, 930), fill='black', width=2)

            self.draw_info(data_db, data_draw, image, day_month, user_id)
            return md.statistics_mes(data_draw)
        except Exception as ex:
            print(ex)
            return None


if __name__ == '__main__':
    pass
