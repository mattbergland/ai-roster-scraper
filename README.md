# Beacons Roster Scraper

A web application that scrapes creator roster data from Beacons.ai and converts it into a CSV file. The application extracts creator names, social media handles, follower counts, and engagement metrics.

## Features

- Extracts creator names and social media information
- Captures social media handles for TikTok, Instagram, and YouTube
- Records engagement rates and demographic data
- Exports data to CSV format
- Web interface for easy use
- Real-time progress tracking
- Automated CSV download

## Requirements

- Python 3.11+
- Chrome browser
- Required Python packages (see requirements.txt)

## Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/beacons_roster_scraper.git
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

4. Run the application:
```bash
python app.py
```

5. Visit http://localhost:5001 in your browser

## Deployment

The application is configured for deployment on Heroku or similar platforms:

1. Create a new Heroku app:
```bash
heroku create your-app-name
```

2. Add buildpacks:
```bash
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-google-chrome
heroku buildpacks:add --index 2 heroku/python
```

3. Deploy the application:
```bash
git push heroku main
```

4. Scale the dynos:
```bash
heroku ps:scale web=1
```

## Usage

1. Visit the deployed application URL
2. Enter a Beacons.ai roster URL
3. Wait for the scraping process to complete (30-45 seconds)
4. The CSV file will automatically download when ready

## Notes

- The application requires a Chrome browser to be installed on the server
- The scraping process takes approximately 30-45 seconds to complete
- A new Chrome window will open during scraping - this is normal and should not be closed
- The application handles one request at a time to ensure stability

## License

MIT License - feel free to use and modify as needed.

## Support

For issues or questions, please open a GitHub issue or contact the maintainer.
