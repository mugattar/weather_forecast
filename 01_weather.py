# -*- coding: utf-8 -*-

import datetime
import re
from engine_module import GetWeatherForecast, DatabaseUpdater


class Weather:
    def __init__(self):
        self.start_date = None
        self.end_date = None
        self.db_updater = None
        self.weather_forecast = None
        self.user_actions = {'1': self.define_dates, '2': self.update_dict, '3': self.update, '4': self.read_db,
                             '5': self.draw_postcards, '6': self.show_weather}
        self.re_date = re.compile(r'^([1-9]|0[1-9]|1[0-9]|2[0-9]|3[0-1])(\.|-|/)([1-9]|0[1-9]|1[0-2])'
                                  r'(\.|-|/)([0-9][0-9]|19[0-9][0-9]|20[0-9][0-9])$')

    def check_date(self, *start_date):
        delta_days = 14
        while True:
            user_date = input('>>>  ')
            match = re.findall(self.re_date, user_date)
            if not match:
                print('Неправильно указана дата. Введите в формате ДД-ММ-ГГГГ', end='')
                continue
            user_date = datetime.datetime.strptime(user_date, '%d-%m-%Y').date()
            if user_date > datetime.date.today() + datetime.timedelta(days=delta_days):
                print(f'Прогноз может быть не более, чем на {delta_days} дней вперед', end='')
            elif start_date and user_date < datetime.datetime.strptime(start_date[0], '%Y-%m-%d').date():
                print(f'Конец диапазона не может быть раньше его начала', end='')
            else:
                return str(user_date)

    def define_dates(self):
        print('Введите начало диапазона в формате ДД-ММ-ГГГГ', end='')
        self.start_date = self.check_date()
        print('Введите конец диапазона в формате ДД-ММ-ГГГГ', end='')
        self.end_date = self.check_date(self.start_date)
        self.db_updater = DatabaseUpdater(self.start_date, self.end_date)

    def update_dict(self):
        GetWeatherForecast().write_to_dict(self.start_date, self.end_date)

    def update(self):
        GetWeatherForecast().write_to_dict(self.start_date, self.end_date)
        self.db_updater.update_db()

    def read_db(self):
        self.weather_forecast = self.db_updater.read_db()

    def draw_postcards(self):
        self.db_updater.draw_postcards()

    def show_weather(self):
        self.db_updater.show_weather()

    def main(self):
        while True:
            print('\nВыберите действие:\n(1) задать диапазон дат\n(2) выгрузить данные из сети\n(3) записать данные в '
                  'базу\n(4) прочитать данные из базы\n(5) создать изображения с погодой\n(6) вывести прогноз погоды '
                  'на экран\n(7) выход\n')
            user_choice = input('>>>  ')
            if '1' in user_choice:
                self.define_dates()
            elif user_choice in self.user_actions and self.start_date:
                self.user_actions[user_choice]()
            elif '7' in user_choice:
                break
            elif self.start_date is None:
                print('Не указан диапазон дат')


if __name__ == '__main__':
    GetWeatherForecast().run()
    Weather().main()