import datetime
import re
import requests
from bs4 import BeautifulSoup
import os
import cv2
import sys
from playhouse.db_url import connect
import models

WEATHER_FORECAST = {}

MONTHS = {1: 'january', 2: 'february', 3: 'march', 4: 'april', 5: 'may', 6: 'june', 7: 'july',
          8: 'august', 9: 'september', 10: 'october', 11: 'november', 12: 'december'}

NUMBER_OF_MONTHS = {'january': '01', 'february': '02', 'march': '03', 'april': '04', 'may': '05',
                    'june': '06', 'july': '07', 'august': '08', 'september': '09', 'october': '10',
                    'november': '11', 'december': '12'}

PICTURE_PATHS = {'sun': 'weather_img\\sun.jpg',
                 'cloud': 'weather_img\\cloud.jpg',
                 'snow': 'weather_img\\snow.jpg',
                 'rain': 'weather_img\\rain.jpg'}

PICTURE_X_OFFSET = 40
PICTURE_Y_OFFSET = 10
DATE_OFFSET = (180, 60)
WEATHER_OFFSET = (30, 220)
TEMPERATURE_OFFSET = (70, 142)
HUMIDITY_OFFSET = (250, 220)
WIND_OFFSET = (30, 190)
PRESSURE_OFFSET = (250, 190)
COLOR_OFFSET = (0, 0, 0)
BACKGROUND_PATH = 'background.jpg'


class WeatherMaker:
    def __init__(self, years, months, start_date):
        self.weather_forecast = WEATHER_FORECAST
        self.years = years
        self.months = months
        self.period_start = start_date

    def run(self):
        for month, year in self.months:
            descriptions = []
            temperatures = []
            humidity_list = []
            wind_list = []
            pressure_list = []
            date_list = []
            response = requests.get(f'https://pogoda.mail.ru/prognoz/sankt_peterburg/{month}-{year}/')
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, features='html.parser')
                day_date = soup.find_all('div', {'class': 'day__date'})
                day_temperature = soup.find_all('div', {'class': 'day__temperature'})
                day_description = soup.find_all('div', {'class': 'day__description'})
                humidity = soup.find_all('span', {'title': re.compile('Влажность:')})
                wind = soup.find_all('span', {'title': re.compile('Ветер:')})
                pressure = soup.find_all('span', {'title': re.compile('Давление:')})

                for day in day_date:
                    date_list.append(' '.join(day.text.split()))
                for desc in day_description:
                    descriptions.append((''.join(desc.text.split())))
                for day in day_temperature:
                    day = ' Ночью '.join(day.text.split())
                    temperatures.append(f'Днем {day}')
                for h in humidity:
                    humidity_list.append((''.join(h.text.split())))
                for w in wind:
                    wind_list.append((' '.join(w.text.split())))
                for p in pressure:
                    pressure_list.append((' '.join(p.text.split())))

                for day, temp, desc, humidity, wind, pressure in zip(date_list, temperatures, descriptions,
                                                                     humidity_list, wind_list, pressure_list):
                    if day[:2] == 'Се':
                        form_day = datetime.date(year=int(year), month=int(NUMBER_OF_MONTHS[month]),
                                                 day=int(day[8:10]))
                    else:
                        form_day = datetime.date(year=int(year), month=int(NUMBER_OF_MONTHS[month]),
                                                 day=int(day[:2]))
                    convert_date = datetime.date(year=int(year), month=int(NUMBER_OF_MONTHS[month]),
                                                 day=int(form_day.day))
                    self.weather_forecast[form_day] = {}
                    self.weather_forecast[form_day]['температура'] = temp
                    self.weather_forecast[form_day]['погода'] = desc
                    self.weather_forecast[form_day]['дата'] = day
                    self.weather_forecast[form_day]['влажность'] = humidity
                    self.weather_forecast[form_day]['ветер'] = wind
                    self.weather_forecast[form_day]['давление'] = pressure
                    self.weather_forecast[form_day]['date'] = str(convert_date)
                    if 'ясно' in self.weather_forecast[form_day]['погода']:
                        self.weather_forecast[form_day]['picture'] = PICTURE_PATHS['sun']
                    elif 'облачно' in self.weather_forecast[form_day]['погода']:
                        self.weather_forecast[form_day]['picture'] = PICTURE_PATHS['cloud']
                    elif 'снег' in self.weather_forecast[form_day]['погода']:
                        self.weather_forecast[form_day]['picture'] = PICTURE_PATHS['snow']
                    else:
                        self.weather_forecast[form_day]['picture'] = PICTURE_PATHS['rain']
            else:
                raise RuntimeError('Запрос не выполнен', response.status_code)


class GetWeatherForecast:
    def __init__(self):
        self.months = []
        self.years = []

    def run(self):
        today_date = datetime.datetime.now()
        start_date = today_date - datetime.timedelta(days=7)
        start = start_date

        while start <= today_date + datetime.timedelta(days=30):
            if MONTHS[start.month] not in self.months:
                self.months.append((MONTHS[start.month], start.year))
            start += datetime.timedelta(days=1)

        weather_maker = WeatherMaker(months=self.months, years=self.years, start_date=start_date)
        weather_maker.run()
        while start_date <= today_date:
            weather_forecast = WEATHER_FORECAST[start_date.date()]
            print(f'{weather_forecast["дата"]}\nтемпература: {weather_forecast["температура"]}, '
                  f'осадки: {weather_forecast["погода"]}, ветер: {weather_forecast["ветер"]}, '
                  f'давление: {weather_forecast["давление"]}, влажность: {weather_forecast["влажность"]}')
            start_date += datetime.timedelta(days=1)

    def write_to_dict(self, start_date, end_date):
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        start = start_date
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

        while start <= end_date + datetime.timedelta(days=30):
            if MONTHS[start.month] not in self.months:
                self.months.append((MONTHS[start.month], start.year))
            start += datetime.timedelta(weeks=4)
        weather_maker = WeatherMaker(months=self.months, years=self.years, start_date=start_date)
        weather_maker.run()

        start_d = start_date
        while start_d <= end_date:
            weather_forecast = WEATHER_FORECAST[start_d]
            print(f'Прогноз на {weather_forecast["дата"]} выгружен из сети')
            start_d += datetime.timedelta(days=1)
        return WEATHER_FORECAST


class ImageMaker:
    def __init__(self, date, temperature, weather, wind, humidity, pressure, picture, day):
        self.date = date
        self.temperature = temperature
        self.weather = weather
        self.wind = wind
        self.humidity = humidity
        self.pressure = pressure
        self.picture = picture
        self.day = day

    def draw_postcard(self):
        image = cv2.imread(BACKGROUND_PATH)
        self.add_gradient(image)
        self.temperature = self.temperature.replace('°', '')
        self.date = self.date.replace('Сегодня', '')
        cv2.putText(image, self.date, DATE_OFFSET, cv2.FONT_HERSHEY_COMPLEX, 1, COLOR_OFFSET)
        cv2.putText(image, self.weather, WEATHER_OFFSET, cv2.FONT_HERSHEY_COMPLEX, 0.8, COLOR_OFFSET)
        cv2.putText(image, self.temperature, TEMPERATURE_OFFSET, cv2.FONT_HERSHEY_COMPLEX, 1, COLOR_OFFSET)
        cv2.putText(image, f'Влажность: {self.humidity}', HUMIDITY_OFFSET, cv2.FONT_HERSHEY_COMPLEX, 0.8, COLOR_OFFSET)
        cv2.putText(image, f'Давление: {self.pressure}', PRESSURE_OFFSET, cv2.FONT_HERSHEY_COMPLEX, 0.8, COLOR_OFFSET)
        cv2.putText(image, f'Ветер: {self.wind}', WIND_OFFSET, cv2.FONT_HERSHEY_COMPLEX, 0.8, COLOR_OFFSET)
        img = cv2.imread(self.picture)
        x_offset = PICTURE_X_OFFSET
        y_offset = PICTURE_Y_OFFSET
        image[y_offset:y_offset + img.shape[0], x_offset:x_offset + img.shape[1]] = img
        image_path = f'images/{self.day}.jpg'
        if not os.path.exists('images'):
            os.mkdir('images')
        cv2.imwrite(image_path, image, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        return image

    def add_gradient(self, image):
        for y in range(255):
            weather_background = {'снег': (255, 255, y),
                                  'ясно': (y, 255, 255),
                                  'облачно': (y + 64, y + 64, y + 64),
                                  'дождь': (255, y, y),
                                  'дождь/гроза': (192, y - 64, y - 64)}
            if self.weather in weather_background:
                weather_state = weather_background[self.weather]
            else:
                weather_state = (y + 64, y + 64, y + 64)
            cv2.line(image, (0, y), (512, y), color=weather_state)


class DatabaseUpdater:
    def __init__(self, start_date, end_date, db_url='sqlite:///weather.db'):
        self.database = connect(db_url)
        models.db.initialize(self.database)
        self.weather = models.Weather
        self.weather.create_table()
        self.start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        self.end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

    def update_db(self):
        start = self.start_date
        while start <= self.end_date:
            value = WEATHER_FORECAST[start]
            db_table = self.weather.get_or_create(day=value['date'], defaults={'date': value['дата'],
                                                                               'temperature': value['температура'],
                                                                               'weather': value['погода'],
                                                                               'wind': value['ветер'],
                                                                               'humidity': value['влажность'],
                                                                               'pressure': value['давление'],
                                                                               'picture': value['picture']})
            if db_table[1] is False:
                update = self.weather.update(day=value['date'], date=value['дата'],
                                             temperature=value['температура'],
                                             weather=value['погода'],
                                             humidity=value['влажность'],
                                             pressure=value['давление'], picture=value['picture']).where(
                    self.weather.id == db_table[0].id)
                update.execute()
            start += datetime.timedelta(days=1)

    def show_weather(self):
        for date in self.weather.select().where(self.weather.day.between(self.start_date, self.end_date)):
            print(date.date, date.temperature, date.weather, date.wind, date.humidity, date.pressure)

    def read_db(self):
        weather = WEATHER_FORECAST
        for date in self.weather.select().where(self.weather.day.between(self.start_date, self.end_date)):
            db_date = datetime.datetime.strptime(date.day, '%Y-%m-%d').date()
            weather[db_date] = {}
            weather[db_date]['температура'] = date.temperature
            weather[db_date]['погода'] = date.weather
            weather[db_date]['дата'] = date.date
            weather[db_date]['влажность'] = date.humidity
            weather[db_date]['ветер'] = date.wind
            weather[db_date]['давление'] = date.pressure
            weather[db_date]['date'] = date.day
            weather[db_date]['picture'] = date.picture
        start = self.start_date
        while start <= self.end_date:
            weather_forecast = weather[start]
            print(f'{weather_forecast["дата"]}\nтемпература: {weather_forecast["температура"]}, осадки: '
                  f'{weather_forecast["погода"]}, ветер: {weather_forecast["ветер"]}, '
                  f'давление:{weather_forecast["давление"]}, влажность:{weather_forecast["влажность"]}')
            start += datetime.timedelta(days=1)
        return weather

    def draw_postcards(self):
        for date in self.weather.select().where(self.weather.day.between(self.start_date, self.end_date)):
            postcard = ImageMaker(date.date, date.temperature, date.weather, date.wind, date.humidity,
                                  date.pressure, date.picture, date.day)
            postcard.draw_postcard()
            sys.stdout.flush()
        print('Изображения сохранены в папке images')
