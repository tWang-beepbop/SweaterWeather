import os
import sys
import requests
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def get_weather_forecast(api_key, latitude, longitude):
    """
    Fetch weather forecast using free Current Weather + 5 Day Forecast APIs
    """
    # Get current weather
    current_url = f"https://api.openweathermap.org/data/2.5/weather"
    current_params = {
        'lat': latitude,
        'lon': longitude,
        'appid': api_key,
        'units': 'metric'  # Use Celsius
    }

    # Get 5-day forecast
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast"
    forecast_params = {
        'lat': latitude,
        'lon': longitude,
        'appid': api_key,
        'units': 'metric'  # Use Celsius
    }

    try:
        # Fetch current weather
        current_response = requests.get(current_url, params=current_params)
        current_response.raise_for_status()
        current_data = current_response.json()

        # Fetch forecast
        forecast_response = requests.get(forecast_url, params=forecast_params)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        # Transform into format similar to One Call API for compatibility
        return {
            'current': {
                'temp': current_data['main']['temp'],
                'feels_like': current_data['main']['feels_like'],
                'humidity': current_data['main']['humidity'],
                'wind_speed': current_data['wind']['speed']
            },
            'daily': [{
                'temp': {
                    'min': current_data['main']['temp_min'],
                    'max': current_data['main']['temp_max']
                },
                'weather': current_data['weather'],
                'pop': forecast_data['list'][0].get('pop', 0) if forecast_data['list'] else 0,
                'humidity': current_data['main']['humidity'],
                'wind_speed': current_data['wind']['speed']
            }]
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        sys.exit(1)


def get_clothing_recommendation(temp_high, temp_low, weather_condition, precipitation_prob, wind_speed_kmh):
    """
    Generate clothing recommendations based on weather conditions (Celsius)
    """
    recommendations = []

    # Temperature-based recommendations (Celsius)
    if temp_high >= 24:
        recommendations.append("Light clothing (t-shirt, shorts/skirt)")
        recommendations.append("Wear light breathable clothing")
    elif temp_high >= 18:
        recommendations.append("Light layers (t-shirt with light jacket)")
    elif temp_high >= 10:
        recommendations.append("Medium layers (long sleeves, sweater or light jacket)")
    elif temp_high >= 4:
        recommendations.append("Warm layers (sweater, jacket)")
    else:
        recommendations.append("Heavy winter clothing (coat, warm layers)")

    # Specific temperature-based clothing reminders
    if 10 <= temp_high <= 14:
        recommendations.append("Wear your white heat tech shirt")

    if temp_high <= 9:
        recommendations.append("Layer your black heat tech shirt with grey merino wool shirt")

    if temp_high < 2:
        recommendations.append("Wear wool socks")

    # Additional recommendations based on conditions
    if temp_low < 4:
        recommendations.append("Bring extra layers for cold mornings/evenings")

    # Rain-specific recommendations
    if 'rain' in weather_condition.lower() or 'drizzle' in weather_condition.lower():
        recommendations.append("Bring an umbrella")
        recommendations.append("Wear a waterproof jacket")
        recommendations.append("Wear waterproof boots")
    elif precipitation_prob > 50:
        recommendations.append("Bring an umbrella or rain jacket")
    elif precipitation_prob > 30:
        recommendations.append("Consider bringing an umbrella")

    if 'snow' in weather_condition.lower():
        recommendations.append("Winter boots and warm accessories (hat, gloves)")

    # Wind-specific recommendations
    if wind_speed_kmh > 15:
        recommendations.append("Wear a hat (windy conditions)")

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
    wind_speed_ms = today.get('wind_speed', current.get('wind_speed', 0))
    wind_speed_kmh = round(wind_speed_ms * 3.6)  # Convert m/s to km/h

    # Get clothing recommendations
    recommendations = get_clothing_recommendation(temp_high, temp_low, weather_main, precipitation_prob, wind_speed_kmh)

    # Build email body
    email_body = f"""Good morning!

Here's your weather forecast and clothing recommendations for today:

WEATHER SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current: {current_temp}°C (feels like {feels_like}°C)
High: {temp_high}°C
Low: {temp_low}°C
Conditions: {weather_desc}
Precipitation chance: {precipitation_prob}%
Humidity: {humidity}%
Wind speed: {wind_speed_kmh} km/h

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

    server = None
    try:
        # Connect to SMTP server
        print(f"Connecting to {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.ehlo()
        print("Starting TLS...")
        server.starttls()
        server.ehlo()
        print("Logging in...")
        server.login(sender_email, sender_password)

        # Send email
        print("Sending email...")
        server.send_message(message)
        print(f"Email sent successfully to {recipient_email}")

    except smtplib.SMTPAuthenticationError as e:
        print(f"Authentication failed: {e}")
        print("Check your email and password/app password are correct")
        sys.exit(1)
    except smtplib.SMTPException as e:
        print(f"SMTP error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error sending email: {e}")
        print(f"Error type: {type(e).__name__}")
        sys.exit(1)
    finally:
        if server:
            try:
                server.quit()
            except:
                pass


def main():
    # Get configuration from environment variables (strip whitespace)
    api_key = os.getenv('OPENWEATHER_API_KEY', '').strip()
    latitude = os.getenv('LATITUDE', '40.7128').strip()
    longitude = os.getenv('LONGITUDE', '-74.0060').strip()

    sender_email = os.getenv('SENDER_EMAIL', '').strip()
    sender_password = os.getenv('SENDER_PASSWORD', '').strip()
    recipient_email = os.getenv('RECIPIENT_EMAIL', sender_email).strip() if os.getenv('RECIPIENT_EMAIL') else sender_email

    # Use 'or' to handle empty strings for SMTP settings
    smtp_server = (os.getenv('SMTP_SERVER') or 'smtp.gmail.com').strip()
    smtp_port = int((os.getenv('SMTP_PORT') or '587').strip())

    # Validate required environment variables
    if not api_key:
        print("Error: OPENWEATHER_API_KEY environment variable is required")
        sys.exit(1)
    if not sender_email or not sender_password:
        print("Error: SENDER_EMAIL and SENDER_PASSWORD environment variables are required")
        sys.exit(1)

    # Debug: Show API key length and first/last few characters (for troubleshooting)
    print(f"API Key length: {len(api_key)}")
    print(f"API Key format check: {api_key[:4]}...{api_key[-4:]}")
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
