# Skyward Grade Tracker

**Access the tool at: [skyward.publicvm.com](http://skyward.publicvm.com)**

## Overview
This tool automatically fetches and calculates GPA data from Skyward, providing both weighted and unweighted GPA calculations for each grading period. Unlike the standard Skyward app that only shows GPA once per semester, this tool gives you continuous GPA tracking and insights.

## Features
- Real-time grade fetching from Skyward
- Automatic GPA calculation (both weighted and unweighted)
- Period-by-period grade tracking
- Support for different course weightings (Regular, APA, AP)
- Visual GPA tracking over time
- Detailed grade breakdowns

## Technical Details

### Technologies Used
- Python
- Flask (Web Framework)
- Selenium WebDriver
- Chrome WebDriver
- HTML/CSS/JavaScript
- Chart.js for data visualization
- Tailwind CSS for styling

### Backend Framework
- Flask for handling web requests and serving content
- Selenium for automated grade fetching
- Gunicorn for production deployment

### GPA Calculation Method
- Regular courses: Base GPA of 6.0
- APA courses: Base GPA of 7.0
- AP courses: Base GPA of 8.0
- For each point below 100, 0.1 is subtracted from the base GPA

### Hosting Information
- Domain: skyward.publicvm.com
- IP Address: 170.9.240.245
- Domain Provider: freedomain.one
- Cloud Platform: Oracle Cloud Infrastructure

## Installation & Setup
### Remote Access
- SSH access via PuTTY to Oracle Cloud VM
- Default SSH port: 22
- Make sure to configure security rules in Oracle Cloud to allow SSH access
  
### Prerequisites
```
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv
sudo apt-get install -y wget unzip xvfb libxi6 libgconf-2-4
```

### Install Chrome and ChromeDriver
```
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

### Python Setup
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Application
```
python app.py
```

## Security Note
Please ensure you keep your Skyward credentials secure and never share them publicly.

## Contributing
Feel free to submit issues and enhancement requests!

## License
[MIT License](LICENSE)
