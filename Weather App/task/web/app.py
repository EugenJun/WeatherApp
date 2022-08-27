import os
import sys
from datetime import datetime, timedelta

import requests
from flask import Flask, request, render_template, redirect, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


db.create_all()


def get_weather(desired_city):
    openweathermap_api = '4f6efa7ef7d5f7e16ea51b3ffaa529c9'
    weather_request = requests.get(
        f'https://api.openweathermap.org/data/2.5/weather?q={desired_city}&units=metric&appid={openweathermap_api}')
    if weather_request.status_code >= 400:
        return None
    time = (datetime.utcnow() + timedelta(hours=weather_request.json()['timezone'] / 3600)).strftime('%H')
    if 0 <= int(time) < 6:
        time_of_day = 'night'
    elif 12 <= int(time) < 18:
        time_of_day = 'day'
    else:
        time_of_day = 'evening-morning'
    return {'temperature': round(weather_request.json()['main']['temp']),
            "weather_state": weather_request.json()['weather'][0]['main'],
            'time_of_day': time_of_day}


@app.route('/')
def index():
    cities_and_weather = dict.fromkeys(
        [City.query.all()[i].name for i in range(len(City.query.all()))])
    for city in cities_and_weather:
        cities_and_weather[city] = get_weather(city)
    return render_template('index.html', cities_and_weather=cities_and_weather)


@app.route('/add', methods=['GET', 'POST'])
def add_city():
    city = City(name=request.form['city_name'])
    if city.name in [City.query.all()[i].name for i in range(len(City.query.all()))]:
        flash("The city has already been added to the list!")
    elif get_weather(city.name) is None:
        flash("The city doesn't exist!")
    else:
        db.session.add(city)
        db.session.commit()
    return redirect('/')


@app.route('/delete/<city>', methods=['GET', 'POST'])
def delete(city):
    city = City.query.filter_by(name=city).first()
    db.session.delete(city)
    db.session.commit()
    return redirect('/')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
