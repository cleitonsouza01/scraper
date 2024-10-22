# scraper
This is a web scraper that I wrote in python. It scrapes the data from the given website. 
It's making use of the BeautifulSoup library to parse the HTML and extract the data also HTTPX to make the HTTP requests. I'm using HTTPX instead of requests because I'll integrate this scraper with my FastAPI project, and HTTPX integrrates better with FastAPI because it's async.


# Requirements
- Python 3
- BeautifulSoup
- httpx
- tenacity

(You can install the required libraries by running the command 'pip install -r requirements.txt')

# Python version
- Python 3.12.5

# How to run the code
- Clone this repository
- Run the following commands in the terminal
```
python -m venv venv
pip install -r requirements.txt
python scraper.py
```

# Output
The output is a valid JSON text. You can use [jq](https://stedolan.github.io/jq/) to enhance the output. 


# Author
- Cleiton Souza