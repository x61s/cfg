#!/bin/bash

API_KEY="---"
CITY="Oskemen"
COUNTRY="KZ"
UNITS="metric"  # or "imperial" for Fahrenheit

# Fetch weather data using OpenWeatherMap API
weather=$(curl -s "http://api.openweathermap.org/data/2.5/weather?q=$CITY,$COUNTRY&appid=$API_KEY&units=$UNITS")

# Parse relevant data using jq
description=$(echo "$weather" | jq -r '.weather[0].description')
temperature=$(echo "$weather" | jq -r '.main.temp')

# Output formatted weather information
echo "$CITY: $description $temperature°C"

