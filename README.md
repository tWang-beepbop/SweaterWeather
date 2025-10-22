# Sweater Weather - Daily Weather Email Automation

Automatically receive a daily email at 7 AM with weather forecasts and clothing recommendations based on current conditions.

## Features

- Fetches weather data from OpenWeather One Call API 3.0
- Provides intelligent clothing recommendations based on temperature, precipitation, and weather conditions
- Sends formatted email via your personal email account (Gmail, Outlook, etc.)
- Runs automatically via GitHub Actions every day at 7 AM
- Easy configuration through GitHub Secrets

## Setup Instructions

### 1. Get an OpenWeather API Key

1. Sign up at [OpenWeather](https://openweathermap.org/)
2. Subscribe to the [One Call API 3.0](https://openweathermap.org/api/one-call-3) plan
3. Copy your API key from your account dashboard

### 2. Get Your Location Coordinates

Find your latitude and longitude:
- Visit [LatLong.net](https://www.latlong.net/)
- Search for your city/address
- Note the latitude and longitude values

### 3. Prepare Your Email Credentials

**For Gmail users:**
1. Enable 2-factor authentication on your Google account
2. Generate an App Password:
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Security > 2-Step Verification > App passwords
   - Create a new app password
   - Copy the 16-character password (this is your `SENDER_PASSWORD`)

**For other email providers:**
- Find your SMTP server and port:
  - **Outlook/Hotmail**: `smtp.office365.com`, port `587`
  - **Yahoo**: `smtp.mail.yahoo.com`, port `587`
  - **Custom domain**: Check with your email provider

### 4. Configure GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret** for each of the following:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `OPENWEATHER_API_KEY` | Your OpenWeather API key | `abc123def456...` |
| `LATITUDE` | Your location latitude | `40.7128` |
| `LONGITUDE` | Your location longitude | `-74.0060` |
| `SENDER_EMAIL` | Your email address | `your.email@gmail.com` |
| `SENDER_PASSWORD` | Your email app password | `abcd efgh ijkl mnop` |
| `RECIPIENT_EMAIL` | Email to receive reports (optional, defaults to sender) | `your.email@gmail.com` |
| `SMTP_SERVER` | SMTP server (optional, defaults to Gmail) | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (optional, defaults to 587) | `587` |

### 5. Adjust the Schedule (Optional)

The workflow runs at 7 AM by default. To change the time:

1. Open [.github/workflows/daily-weather-email.yml](.github/workflows/daily-weather-email.yml)
2. Modify the cron schedule:
   ```yaml
   schedule:
     - cron: '0 12 * * *'  # Change this line
   ```

**Cron format:** `minute hour * * *`
- All times are in **UTC**
- For 7 AM EST: `0 12 * * *` (UTC+5)
- For 7 AM PST: `0 15 * * *` (UTC+8)
- For 7 AM CST: `0 13 * * *` (UTC+6)

Use [crontab.guru](https://crontab.guru/) to help generate cron expressions.

### 6. Test the Setup

You can manually trigger the workflow to test:

1. Go to **Actions** tab in your GitHub repository
2. Click **Daily Weather Email** workflow
3. Click **Run workflow** > **Run workflow**
4. Check your email in a few minutes

## Project Structure

```
SweaterWeather/
├── .github/
│   └── workflows/
│       └── daily-weather-email.yml    # GitHub Actions workflow
├── weather_emailer.py                  # Main Python script
├── requirements.txt                    # Python dependencies
└── README.md                          # This file
```

## How It Works

1. **GitHub Actions** triggers the workflow daily at 7 AM (UTC)
2. The workflow sets up Python and installs dependencies
3. **weather_emailer.py** runs with your configured secrets:
   - Fetches current weather and forecast from OpenWeather API
   - Analyzes temperature, precipitation, and conditions
   - Generates clothing recommendations
   - Sends a formatted email via SMTP

## Clothing Recommendation Logic

The script recommends clothing based on:

- **Temperature ranges**: Light, medium, warm, or heavy clothing
- **Precipitation probability**: Umbrella and rain gear suggestions
- **Weather conditions**: Snow boots, waterproof shoes, etc.
- **Temperature variation**: Layer recommendations for large temp swings
- **Cold mornings**: Extra layers for low overnight temperatures

## Troubleshooting

**Workflow fails with authentication error:**
- For Gmail: Ensure you're using an App Password, not your regular password
- For other providers: Verify SMTP server and port are correct

**No weather data received:**
- Verify your OpenWeather API key is valid and has One Call API 3.0 access
- Check that latitude/longitude are in correct decimal format

**Emails not arriving:**
- Check spam/junk folder
- Verify RECIPIENT_EMAIL is set correctly
- Review GitHub Actions logs for error messages

**Wrong timezone:**
- Remember GitHub Actions uses UTC time
- Adjust the cron schedule accordingly

## Local Testing

To test locally before setting up GitHub Actions:

```bash
# Set environment variables (Windows PowerShell)
$env:OPENWEATHER_API_KEY="your-api-key"
$env:LATITUDE="40.7128"
$env:LONGITUDE="-74.0060"
$env:SENDER_EMAIL="your.email@gmail.com"
$env:SENDER_PASSWORD="your-app-password"

# Install dependencies
pip install -r requirements.txt

# Run the script
python weather_emailer.py
```

## License

This project is open source and available for personal use.
