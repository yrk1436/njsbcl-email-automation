# Biweekly Task Automation

A Python application that automates the biweekly task of scraping cricket game schedules, finding team contacts, and scheduling invitation emails for SPARTA XI cricket team.

## Features

- **Web Scraping**: Scrapes HTML pages to extract game schedules and team contacts
- **Email Automation**: Sends personalized invitation emails using Gmail API
- **Smart Scheduling**: Automatically calculates the Tuesday before Sunday games for email scheduling
- **Error Handling**: Comprehensive logging and error handling for production use
- **Modular Design**: Clean, maintainable code structure

## Requirements

- Python 3.12+
- uv package manager
- Gmail API credentials
- Internet connection for web scraping

## Installation

### Prerequisites

1. **Install uv** (if not already installed):
   ```bash
   # On macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Or using pip
   pip install uv
   ```

2. **Clone or download the project files**

### Setup

1. **Install dependencies with uv**:
   ```bash
   uv sync
   ```

2. **Activate the virtual environment**:
   ```bash
   uv shell
   ```

3. **Set up Gmail API credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download the credentials JSON file
   - Rename it to `credentials.json` and place it in the project root

4. **Configure the application**:
   - Update URLs in `config.py` to match your actual schedule and contacts pages
   - Customize the email template in `email_template.html` if needed
   - Adjust team name and other settings in `config.py`

## Usage

### Basic Usage

Run the automation:
```bash
# Make sure you're in the uv shell
uv shell

# Run the application
python main.py
```

### Configuration

Edit `config.py` to customize:

- **URLs**: Update `SCHEDULE_URL` and `CONTACTS_URL` to your actual pages
- **Team Information**: Modify `TEAM_NAME` and `SPARTA_MAP_LINK`
- **Email Settings**: Adjust email timing and template file paths
- **Logging**: Configure log level and format

### Email Template

The email template (`email_template.html`) supports these placeholders:
- `{DATE}`: Game date (e.g., "Sunday, July 27")
- `{OPPONENT_TEAM}`: Opponent team name
- `{MAP_LINK}`: Link to Sparta ground

## How It Works

1. **Schedule Scraping**: 
   - Fetches the schedule page
   - Identifies future Sunday games for SPARTA XI
   - Extracts opponent team names and game dates

2. **Contact Lookup**:
   - For each opponent team, scrapes the contacts page
   - Finds the team's email address

3. **Email Scheduling**:
   - Calculates the Tuesday before each Sunday game
   - Schedules invitation emails for 7:00 PM ET on that Tuesday
   - Uses personalized HTML template with dynamic content

4. **Validation**:
   - Skips games that are not on Sundays
   - Validates all data before processing
   - Comprehensive error handling and logging

## File Structure

```
njsbcl/
├── main.py                 # Main application entry point
├── config.py              # Configuration settings
├── scraper.py             # Web scraping functionality
├── email_manager.py       # Gmail API and email management
├── email_template.html    # HTML email template
├── pyproject.toml        # Project configuration and dependencies
├── README.md             # This file
├── credentials.json      # Gmail API credentials (you need to add this)
├── token.json           # Gmail API token (auto-generated)
└── biweekly_task.log    # Application logs (auto-generated)
```

## Customization

### HTML Scraping

The scraper uses placeholder selectors that need to be customized for your actual HTML structure:

**In `scraper.py`**:
- Update `game_entries` selector to match your schedule page structure
- Modify `opponent_selectors` and `date_selectors` for your HTML
- Adjust `team_entries` and email extraction logic for contacts page

### Email Template

Customize `email_template.html` to match your team's branding and messaging.

### Scheduling Logic

Modify `calculate_send_date()` in `email_manager.py` if you need different scheduling rules.

## Troubleshooting

### Common Issues

1. **Gmail API Authentication**:
   - Ensure `credentials.json` is in the project root
   - First run will open browser for OAuth authentication
   - Check that Gmail API is enabled in Google Cloud Console

2. **Web Scraping Issues**:
   - Verify URLs in `config.py` are correct
   - Check if websites block automated requests
   - Consider using a proxy or different User-Agent

3. **No Games Found**:
   - Verify the schedule page contains SPARTA XI games
   - Check that games are scheduled for Sundays
   - Ensure games are in the future

4. **Email Not Sent**:
   - Check Gmail API quotas and limits
   - Verify recipient email addresses are valid
   - Review logs for specific error messages

### Logs

The application creates detailed logs in `biweekly_task.log`. Check this file for:
- Scraping results and errors
- Email scheduling status
- Authentication issues
- General application flow

### Debug Mode

To enable debug logging, modify `config.py`:
```python
LOG_LEVEL = "DEBUG"
```

## Production Deployment

### Cron Job Setup

To run automatically every week:
```bash
# Add to crontab (runs every Tuesday at 6:00 PM)
0 18 * * 2 cd /path/to/project && uv run python main.py
```

### Environment Variables

Consider using environment variables for sensitive data:
```python
import os
SCHEDULE_URL = os.getenv('SCHEDULE_URL', 'https://xyz.com/schedule')
```

## Security Considerations

- Keep `credentials.json` and `token.json` secure
- Don't commit credentials to version control
- Use environment variables for sensitive data
- Regularly rotate Gmail API credentials

## License

This project is for internal use. Please ensure compliance with website terms of service for web scraping activities. 