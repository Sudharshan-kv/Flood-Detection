import time
import Adafruit_DHT
import Adafruit_CharLCD as LCD
import RPi.GPIO as GPIO
import spidev
import mysql.connector
import requests
from twilio.rest import Client

# Twilio configuration
ACCOUNT_SID = "AC1e68e4e4c757fca2e425fe013462050d"
AUTH_TOKEN = "f1235acdb4299cb9e36c17b68a0a4516"
TWILIO_PHONE_NUMBER = "+16812068965"
TO_PHONE_NUMBER = "+919535569275"

# ThingSpeak API configuration
THINGSPEAK_WRITE_API_KEY = "YOUR_API_KEY"  # Replace with your API key
THINGSPEAK_URL = "https://api.thingspeak.com/update"

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",  # Replace with your password
    "database": "flood_detection"
}

# GPIO Pin configuration
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 17
TRIG_PIN = 23
ECHO_PIN = 24
BUZZER_PIN = 18
GREEN_LED_PIN = 17
YELLOW_LED_PIN = 27
RED_LED_PIN = 22

# LCD configuration
lcd_rs = 26
lcd_en = 19
lcd_d4 = 13
lcd_d5 = 6
lcd_d6 = 5
lcd_d7 = 11
lcd_columns = 16
lcd_rows = 2

# MCP3008 configuration
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000
RAIN_SENSOR_CHANNEL = 0

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
GPIO.setup(YELLOW_LED_PIN, GPIO.OUT)
GPIO.setup(RED_LED_PIN, GPIO.OUT)

# Initialize the LCD
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)

# Initialize Twilio client
client = Client(ACCOUNT_SID, AUTH_TOKEN)

# Flags
sms_sent = False
buzzer_triggered = False
sensor_active = True  # Variable to control sensor operation

def read_adc(channel):
    if channel < 0 or channel > 7:
        return -1
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

def read_distance():
    GPIO.output(TRIG_PIN, False)
    time.sleep(0.1)
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    start_time = time.time()
    stop_time = time.time()

    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()

    while GPIO.input(ECHO_PIN) == 1:
        stop_time = time.time()

    duration = stop_time - start_time
    distance = (duration * 34300) / 2
    return round(distance, 2)

def read_rain_status():
    rain_value = read_adc(RAIN_SENSOR_CHANNEL)
    if rain_value > 800:
        return "No Rain"
    elif 300 < rain_value <= 800:
        return "Light Rain"
    else:
        return "Heavy Rain"

def control_led(distance):
    if distance > 7:
        GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
        GPIO.output(YELLOW_LED_PIN, GPIO.LOW)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
        return 1 
    elif 4 <= distance <= 7:
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        GPIO.output(YELLOW_LED_PIN, GPIO.HIGH)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
        return 2 
    else:
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        GPIO.output(YELLOW_LED_PIN, GPIO.LOW)
        GPIO.output(RED_LED_PIN, GPIO.HIGH)
        return 3 

try:
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()

    while True:
        if sensor_active:
            distance = read_distance()
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            rain_status = read_rain_status()
            led_status = control_led(distance)

            print(f"Distance: {distance} cm, Temp: {temperature}°C, Humidity: {humidity}%, Rain: {rain_status}")

            lcd.clear()
            lcd.message(f"Dist: {distance} cm\n")
            time.sleep(2)
            lcd.clear()
            lcd.message(f"Temp: {temperature}°C\nHumidity: {humidity}%")
            time.sleep(2)
            lcd.clear()
            lcd.message(f"Rain: {rain_status}")
            time.sleep(2)

            if distance < 4 and not buzzer_triggered:
                print("Critical condition detected!")
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                time.sleep(5)
                GPIO.output(BUZZER_PIN, GPIO.LOW)
                buzzer_triggered = True

                if not sms_sent:
                    try:
                        message = client.messages.create(
                            body="Emergency Alert! Water level critical. Immediate action needed.",
                            from_=TWILIO_PHONE_NUMBER,
                            to=TO_PHONE_NUMBER
                        )
                        print(f"SMS sent successfully: {message.sid}")
                        sms_sent = True
                    except Exception as e:
                        print(f"Error sending SMS: {e}")

            if humidity is not None and temperature is not None:
                cursor.execute(
                    """
                    INSERT INTO sensor_data (temperature, humidity, distance, rain_status, led_status)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (temperature, humidity, distance, rain_status, led_status)
                )
                db.commit()

            requests.post(THINGSPEAK_URL, data={
                "api_key": THINGSPEAK_WRITE_API_KEY,
                "field1": temperature,
                "field2": humidity,
                "field3": distance,
                "field4": 1 if distance < 4 else 0,
                "field5": 1 if rain_status in ["Light Rain", "Heavy Rain"] else 0,
                "field6": led_status
            })

            if distance >= 4:
                buzzer_triggered = False
                sms_sent = False
                sensor_active = True

            time.sleep(10)

except KeyboardInterrupt:
    print("\nExiting program.")
finally:
    lcd.clear()
    GPIO.cleanup()
    db.close()
    spi.close()
