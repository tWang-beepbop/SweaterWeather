import os
import sys
import requests
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def get_weather_forecast(api_key, latitude, longitude):
    """
    Fetch weather forecast from OpenWeather One Call API 3.0
    """
    url = f"https://api.openweathermap.org/data/3.0/onecall"
    params = {
        'lat': latitude,
        'lon': longitude,
        'appid': api_key,
        'units': 'imperial',  # Use Fahrenheit
        'exclude': 'minutely,hourly,alerts'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        sys.exit(1)


def get_clothing_recommendation(temp_high, temp_low, weather_condition, precipitation_prob):
    """
    Generate clothing recommendations based on weather conditions
    """
    recommendations = []

    # Temperature-based recommendations
    if temp_high >= 75:
        recommendations.append("Light clothing (t-shirt, shorts/skirt)")
    elif temp_high >= 65:
        recommendations.append("Light layers (t-shirt with light jacket)")
    elif temp_high >= 50:
        recommendations.append("Medium layers (long sleeves, sweater or light jacket)")
    elif temp_high >= 40:
        recommendations.append("Warm layers (sweater, jacket)")
    else:
        recommendations.append("Heavy winter clothing (coat, warm layers)")

    # Additional recommendations based on conditions
    if temp_low < 40:
        recommendations.append("Bring extra layers for cold mornings/evenings")

    if precipitation_prob > 50:
        recommendations.append("Bring an umbrella or rain jacket")
    elif precipitation_prob > 30:
        recommendations.append("Consider bringing an umbrella")

    if 'rain' in weather_condition.lower() or 'drizzle' in weather_condition.lower():
        recommendations.append("Waterproof shoes recommended")

    if 'snow' in weather_condition.lower():
        recommendations.append("Winter boots and warm accessories (hat, gloves)")

    if temp_high - temp_low > 20:
        recommendations.append("Temperature varies significantly - dress in layers")

    return recommendations


def create_email_body(weather_data):
    """
    Create formatted email body with weather info and clothing recommendations
    """
    today = weather_data['daily'][0]
    current = weather_data['current']

    temp_high = round(today['temp']['max'])
    temp_low = round(today['temp']['min'])
    current_temp = round(current['temp'])
    feels_like = round(current['feels_like'])
    weather_main = today['weather'][0]['main']
    weather_desc = today['weather'][0]['description'].capitalize()
    precipitation_prob = round(today.get('pop', 0) * 100)
    humidity = today.get('humidity', current.get('humidity', 0))
    wind_speed = round(today.get('wind_speed', current.get('wind_speed', 0)))

    # Get clothing recommendations
    recommendations = get_clothing_recommendation(temp_high, temp_low, weather_main, precipitation_prob)

    # Build email body
    email_body = f"""Good morning!

Here's your weather forecast and clothing recommendations for today:

WEATHER SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current: {current_temp}°F (feels like {feels_like}°F)
High: {temp_high}°F
Low: {temp_low}°F
Conditions: {weather_desc}
Precipitation chance: {precipitation_prob}%
Humidity: {humidity}%
Wind speed: {wind_speed} mph

WHAT TO WEAR TODAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    for i, rec in enumerate(recommendations, 1):
        email_body += f"{i}. {rec}\n"

    email_body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Have a great day!

---
Generated on {datetime.now().strftime('%Y-%m-%d at %I:%M %p')}
"""

    return email_body


def send_email(sender_email, sender_password, recipient_email, subject, body, smtp_server, smtp_port):
    """
    Send email using SMTP
    """
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject

    message.attach(MIMEText(body, 'plain'))

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)

        # Send email
        server.send_message(message)
        server.quit()

        print(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
        sys.exit(1)


def main():
    # Get configuration from environment variables (strip whitespace)
    api_key = os.getenv('OPENWEATHER_API_KEY', '').strip()
    latitude = os.getenv('LATITUDE', '40.7128').strip()
    longitude = os.getenv('LONGITUDE', '-74.0060').strip()

    sender_email = os.getenv('SENDER_EMAIL', '').strip()
    sender_password = os.getenv('SENDER_PASSWORD', '').strip()
    recipient_email = os.getenv('RECIPIENT_EMAIL', sender_email).strip() if os.getenv('RECIPIENT_EMAIL') else sender_email

    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com').strip()
    smtp_port = int((os.getenv('SMTP_PORT') or '587').strip())

    # Validate required environment variables
    if not api_key:
        print("Error: OPENWEATHER_API_KEY environment variable is required")
        sys.exit(1)
    if not sender_email or not sender_password:
        print("Error: SENDER_EMAIL and SENDER_PASSWORD environment variables are required")
        sys.exit(1)

    print(f"Fetching weather for coordinates: {latitude}, {longitude}")

    # Get weather data
    weather_data = get_weather_forecast(api_key, latitude, longitude)

    # Create email content
    email_body = create_email_body(weather_data)
    subject = f"Your Daily Weather & Outfit Guide - {datetime.now().strftime('%B %d, %Y')}"

    # Send email
    send_email(sender_email, sender_password, recipient_email, subject, email_body, smtp_server, smtp_port)


if __name__ == "__main__":
    main()
