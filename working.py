import RPi.GPIO as GPIO
import time
import spidev
import requests
import board
import busio
import adafruit_bmp280

# Setup GPIO
GPIO.setmode(GPIO.BCM)

# Firebase URL
FIREBASE_URL = "https://ifsp1-07239-default-rtdb.asia-southeast1.firebasedatabase.app/sensorData.json"

# SPI for MCP3008
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

# BMP280 Setup (Adafruit Library)
i2c = busio.I2C(board.SCL, board.SDA)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)

# Optional: Set sea level pressure for accurate altitude if needed
# bmp280.sea_level_pressure = 1013.25

# MCP3008 analog read
def read_analog(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def convert_volts(data, places=2):
    volts = (data * 3.3) / 1023.0
    return round(volts, places)

# Firebase send
def send_data_to_firebase(data):
    try:
        response = requests.put(FIREBASE_URL, json=data)
        if response.status_code == 200:
            print("✅ Data sent to Firebase.")
        else:
            print(f"❌ Failed to send data: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Error sending data to Firebase: {e}")

# Main loop
try:
    while True:
        # Analog sensor readings
        mq135 = convert_volts(read_analog(0))
        mq9 = convert_volts(read_analog(1))
        syh2r = convert_volts(read_analog(2))

        print(f"MQ135 (NH3): {mq135:.2f} V")
        print(f"MQ9 (CO): {mq9:.2f} V")
        print(f"SYH-2R Moisture: {syh2r:.2f} V")

        # BMP280 readings
        temperature = bmp280.temperature
        pressure = bmp280.pressure

        print(f"BMP280 Temperature: {temperature:.2f} °C")
        print(f"BMP280 Pressure: {pressure:.2f} hPa")

        # Combine all into one payload
        payload = {
            "mq135": mq135,
            "mq9": mq9,
            "syh2r": syh2r,
            "bmp280_temperature": round(temperature, 2),
            "bmp280_pressure_hpa": round(pressure, 2)
        }

        # Send to Firebase once
        send_data_to_firebase(payload)

        print("---- Waiting 5 seconds ----\n")
        time.sleep(5)

except KeyboardInterrupt:
    print("🔁 Stopping... Cleaning up.")
    GPIO.cleanup()
