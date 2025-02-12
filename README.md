# Beacons Roster Scraper

A web application that scrapes creator roster data from Beacons.ai and converts it into a CSV file for easy import into spreadsheets.

## Features

- Simple web interface for inputting Beacons.ai roster URLs
- Automatically scrapes creator data
- Generates downloadable CSV files
- Error handling and user feedback
- Mobile-responsive design

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:5000`
3. Paste a Beacons.ai roster URL (format: https://beacons.ai/management/[org-id]/roster/all-creators)
4. Click "Generate CSV" to download the roster data

## Requirements

- Python 3.7+
- Flask
- Requests
- BeautifulSoup4
- Pandas

## License

MIT License
