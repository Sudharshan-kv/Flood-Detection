using Raspberry pi

This project is a real-time flood detection and alert system using a Raspberry Pi, ultrasonic sensor, rain sensor, DHT11 temperature and humidity sensor, buzzer, LEDs, and an LCD display. It sends SMS alerts using Twilio and logs data to a MySQL database and ThingSpeak.

Features Measures water level using an ultrasonic sensor. Monitors rainfall using a rain sensor. Reads temperature and humidity using a DHT11 sensor. Visual indication using Green, Yellow, and Red LEDs. Audible buzzer alert in critical conditions. Sends emergency SMS alerts using Twilio. Logs sensor data into a MySQL database. Sends sensor data to ThingSpeak cloud.

Hardware Components Raspberry Pi, Ultrasonic Sensor (HC-SR04), Rain Sensor (YL-83 with MCP3008 ADC), DHT11 Temperature & Humidity Sensor, Buzzer, LEDs (Green, Yellow, Red), 16x2 LCD Display, MCP3008 ADC (for analog input), Jumper wires, Breadboard

Software Requirements Python 3, RPi.GPIO, Adafruit_DHT library, Adafruit_CharLCD library, spidev library, MySQL Connector, Twilio library, Requests library

Setup Instructions

Wire all sensors and components as per the pin configuration in the code.

Install required Python libraries: sudo apt-get update sudo apt-get install python3-pip pip3 install RPi.GPIO Adafruit_DHT mysql-connector-python twilio requests spidev

Setup MySQL database with a table sensor_data: CREATE DATABASE flood_detection; USE flood_detection; CREATE TABLE sensor_data ( id INT AUTO_INCREMENT PRIMARY KEY, temperature FLOAT, humidity FLOAT, distance FLOAT, rain_status VARCHAR(20), led_status INT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP );

Replace placeholders in the code: Twilio ACCOUNT_SID, AUTH_TOKEN, TWILIO_PHONE_NUMBER, TO_PHONE_NUMBER ThingSpeak THINGSPEAK_WRITE_API_KEY Database password in DB_CONFIG

Run the program: python3 flood_detection.py

Working:

Ultrasonic sensor measures the distance to water.
Rain sensor detects rain intensity.
DHT11 measures temperature and humidity.
LEDs indicate water level: Green: Safe (> 7 cm) Yellow: Caution (4-7 cm) Red: Danger (< 4 cm)
Buzzer and SMS alert on critical water level.
Data is stored in MySQL and sent to ThingSpeak.# Flood-Detection
