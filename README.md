# Beacons Roster Scraper

A web application that scrapes creator roster data from Beacons.ai and converts it into a CSV file. The application extracts creator names, social media handles, follower counts, and engagement metrics.

## Features

- Extracts creator names and social media information
- Captures follower counts for TikTok, Instagram, and YouTube
- Records engagement rates and demographic data
- Exports data to CSV format
- Web interface for easy use

## Requirements

- Python 3.8+
- Chrome browser
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd beacons_roster_scraper
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:5001`

3. Enter a Beacons.ai roster URL and click "Generate CSV"

4. The application will scrape the data and provide a CSV file for download

## Data Format

The CSV output includes:
- Name
- Instagram handle and followers
- TikTok handle and followers
- YouTube subscribers
- Engagement rate
- Gender demographics
- Age demographics

## License

MIT License
