import os
import sys
import requests
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage


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

    if temp_high < 5:
        recommendations.append("Wear a toque and scarf")

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

    # Sunny day recommendations
    if 'clear' in weather_condition.lower() or 'sun' in weather_condition.lower():
        recommendations.append("Wear sunscreen")

    # Wind-specific recommendations (only for cooler temperatures, but not if toque already recommended)
    if wind_speed_kmh > 15 and temp_high < 18 and temp_high >= 5:
        recommendations.append("Wear a toque (windy conditions)")

    if temp_high - temp_low > 20:
        recommendations.append("Temperature varies significantly - dress in layers")

    return recommendations


def get_weather_icon_path(weather_condition):
    """
    Determine which weather icon to use based on conditions
    Priority: thunderstorm > snow > rain > clouds > clear
    """
    weather_lower = weather_condition.lower()

    # Get the script directory to build absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Check for severe weather first (highest priority)
    if 'thunderstorm' in weather_lower or 'thunder' in weather_lower:
        return os.path.join(script_dir, 'thunder.png')
    elif 'snow' in weather_lower or 'sleet' in weather_lower or 'flurr' in weather_lower:
        return os.path.join(script_dir, 'snow.png')
    elif 'rain' in weather_lower or 'drizzle' in weather_lower:
        return os.path.join(script_dir, 'rainy cloud.png')
    elif 'cloud' in weather_lower:
        # Check if it's partly cloudy
        if 'few' in weather_lower or 'scattered' in weather_lower or 'partly' in weather_lower:
            return os.path.join(script_dir, 'partly sunny.png')
        else:
            return os.path.join(script_dir, 'cloudy.png')
    elif 'clear' in weather_lower or 'sun' in weather_lower:
        return os.path.join(script_dir, 'sun.png')
    else:
        # Default to partly sunny for unknown conditions
        return os.path.join(script_dir, 'partly sunny.png')


def create_email_body(weather_data):
    """
    Create formatted email body with weather info and clothing recommendations
    Returns tuple of (text_body, html_body, icon_path)
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

    # Get weather icon
    icon_path = get_weather_icon_path(weather_desc)

    # Check if we need windy icon
    script_dir = os.path.dirname(os.path.abspath(__file__))
    windy_icon_path = os.path.join(script_dir, 'windy.png') if wind_speed_kmh > 20 else None

    # Build text email body (fallback)
    text_body = f"""Good morning!

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
        text_body += f"{i}. {rec}\n"

    text_body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Have a great day!

---
Generated on {datetime.now().strftime('%Y-%m-%d at %I:%M %p')}
"""

    # Build HTML email body (with image)
    recommendations_html = "".join([f"<li>{rec}</li>" for rec in recommendations])

    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .weather-icon {{ text-align: center; margin: 20px 0; }}
            .weather-icon img {{ max-width: 200px; height: auto; }}
            .weather-summary {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .weather-summary h2 {{ margin-top: 0; color: #2c3e50; }}
            .weather-detail {{ margin: 10px 0; }}
            .recommendations {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; }}
            .recommendations h2 {{ margin-top: 0; color: #2c3e50; }}
            ul {{ padding-left: 20px; }}
            li {{ margin: 8px 0; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Good morning!</h1>
            <p>Here's your weather forecast and clothing recommendations for today:</p>

            <div class="weather-icon">
                <img src="cid:weather_icon" alt="Weather Icon">
                {"<img src='cid:windy_icon' alt='Windy' style='margin-left: 10px;'>" if wind_speed_kmh > 20 else ""}
            </div>

            <div class="weather-summary">
                <h2>Weather Summary</h2>
                <div class="weather-detail"><strong>Current:</strong> {current_temp}°C (feels like {feels_like}°C)</div>
                <div class="weather-detail"><strong>High:</strong> {temp_high}°C</div>
                <div class="weather-detail"><strong>Low:</strong> {temp_low}°C</div>
                <div class="weather-detail"><strong>Conditions:</strong> {weather_desc}</div>
                <div class="weather-detail"><strong>Precipitation chance:</strong> {precipitation_prob}%</div>
                <div class="weather-detail"><strong>Humidity:</strong> {humidity}%</div>
                <div class="weather-detail"><strong>Wind speed:</strong> {wind_speed_kmh} km/h</div>
            </div>

            <div class="recommendations">
                <h2>What to Wear Today</h2>
                <ul>
                    {recommendations_html}
                </ul>
            </div>

            <p><strong>Have a great day!</strong></p>

            <div class="footer">
                Generated on {datetime.now().strftime('%Y-%m-%d at %I:%M %p')}
            </div>
        </div>
    </body>
    </html>
    """

    return text_body, html_body, icon_path, windy_icon_path


def send_email(sender_email, sender_password, recipient_email, subject, text_body, html_body, icon_path, windy_icon_path, smtp_server, smtp_port):
    """
    Send email using SMTP with both text and HTML parts and embedded images
    """
    message = MIMEMultipart('related')
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject

    # Create alternative part for text and HTML
    msg_alternative = MIMEMultipart('alternative')
    message.attach(msg_alternative)

    # Attach text and HTML parts
    msg_alternative.attach(MIMEText(text_body, 'plain'))
    msg_alternative.attach(MIMEText(html_body, 'html'))

    # Attach the weather icon image
    try:
        with open(icon_path, 'rb') as img_file:
            img_data = img_file.read()
            img = MIMEImage(img_data)
            img.add_header('Content-ID', '<weather_icon>')
            img.add_header('Content-Disposition', 'inline', filename=os.path.basename(icon_path))
            message.attach(img)
    except FileNotFoundError:
        print(f"Warning: Weather icon not found at {icon_path}. Email will be sent without icon.")
    except Exception as e:
        print(f"Warning: Could not attach weather icon: {e}. Email will be sent without icon.")

    # Attach the windy icon if wind speed is high
    if windy_icon_path:
        try:
            with open(windy_icon_path, 'rb') as img_file:
                img_data = img_file.read()
                img = MIMEImage(img_data)
                img.add_header('Content-ID', '<windy_icon>')
                img.add_header('Content-Disposition', 'inline', filename=os.path.basename(windy_icon_path))
                message.attach(img)
        except FileNotFoundError:
            print(f"Warning: Windy icon not found at {windy_icon_path}. Email will be sent without windy icon.")
        except Exception as e:
            print(f"Warning: Could not attach windy icon: {e}. Email will be sent without windy icon.")

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
    text_body, html_body, icon_path, windy_icon_path = create_email_body(weather_data)
    subject = f"Your Daily Weather & Outfit Guide - {datetime.now().strftime('%B %d, %Y')}"

    # Send email
    send_email(sender_email, sender_password, recipient_email, subject, text_body, html_body, icon_path, windy_icon_path, smtp_server, smtp_port)


if __name__ == "__main__":
    main()
