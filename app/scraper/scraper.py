import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, parse_qs, urlparse
import re
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError

from app.logging_config import logger

THIRD_PARTY_API_URL = 'https://my-third-party-api.com/api/v1/scrape'

# Helper function to extract phone numbers using regex
def extract_phone_numbers(text):
    phone_regex = re.compile(
        r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
    )
    matches = phone_regex.findall(text)
    clean_numbers = [''.join(match).strip() for match in matches if len(''.join(match).strip()) >= 10]
    return clean_numbers

# Helper function to extract phone numbers from specific HTML elements
def extract_phone_numbers_from_elements(soup):
    text_elements = soup.find_all(['p', 'span', 'div'])  # Scan common elements for phone numbers
    phone_numbers = []
    for element in text_elements:
        element_text = element.get_text(separator=' ', strip=True)
        phone_numbers += extract_phone_numbers(element_text)
    return phone_numbers

# Helper function to extract social media links from the page
def extract_social_links(soup):
    social_networks = {
        'instagram': 'instagram.com',
        'facebook': 'facebook.com',
        'twitter': 'twitter.com',
        'linkedin': 'linkedin.com',
        'youtube': 'youtube.com',
        'tiktok': 'tiktok.com',
        'pinterest': 'pinterest.com',
        'whatsapp': 'wa.me',
        'snapchat': 'snapchat.com'
    }

    social_links = {}
    for link in soup.find_all('a', href=True):
        href = link['href']
        for network, pattern in social_networks.items():
            if pattern in href:
                social_links[network] = href
    return social_links

# Use tenacity to handle retries
@retry(stop=stop_after_attempt(2), wait=wait_fixed(2))  # Retry 1 time to improve speed
async def fetch_url(client, url, headers):
    response = await client.get(url, headers=headers)
    response.raise_for_status()  # This will raise an HTTPStatusError if the status code is 4xx or 5xx
    return response

async def fetch_metadata_from_url(client, url, headers):
    response = await fetch_url(client, url, headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract title, description, favicon
    title = soup.find('title').text if soup.find('title') else None
    description = soup.find('meta', attrs={'name': 'description'})
    description = description['content'] if description else None
    favicon = soup.find('link', rel='icon')
    favicon = urljoin(url, favicon['href']) if favicon else None

    # Extract email addresses
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?!\.(png|jpg|jpeg|gif|bmp|svg|css|js))", response.text)
    emails = list(filter(None, emails))

    # Extract phone numbers from both text and specific elements
    phone_numbers = extract_phone_numbers(response.text)
    phone_numbers += extract_phone_numbers_from_elements(soup)

    # Extract social media links
    social_links = extract_social_links(soup)

    return title, description, favicon, emails, phone_numbers, social_links

async def fetch_metadata_from_third_party(client, url):
    third_party_api_url = f{THIRD_PARTY_API_URL}={url}"
    response = await client.get(third_party_api_url)
    if response.status_code != 200:
        logger.error(f"Failed to fetch {url} even with third-party API: {response.text}")
        return None
    original_response = response.json()
    data = original_response.get('body', {})

    # Extract metadata from JSON response
    title = data.get('title')
    description = data.get('meta', {}).get('description')
    favicon = data.get('favicon')

    # Extract email addresses from the 'links' and 'content'
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?!\.(png|jpg|jpeg|gif|bmp|svg|css|js))", data.get('content', ''))
    for link in data.get('links', []):
        emails += re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?!\.(png|jpg|jpeg|gif|bmp|svg|css|js))", link)
    emails = list(filter(None, emails))

    # Extract phone numbers by scanning all text fields in the JSON response
    phone_numbers = extract_phone_numbers(data.get('content', ''))

    # Extract social media links from JSON response by scanning 'links'
    social_links = {}
    social_networks = {
        'instagram': 'instagram.com',
        'facebook': 'facebook.com',
        'twitter': 'twitter.com',
        'linkedin': 'linkedin.com',
        'youtube': 'youtube.com',
        'tiktok': 'tiktok.com',
        'pinterest': 'pinterest.com',
        'whatsapp': 'wa.me',
        'snapchat': 'snapchat.com'
    }
    for link in data.get('links', []):
        parsed_url = urlparse(link)
        if 'whatsapp' in parsed_url.netloc:
            query_params = parse_qs(parsed_url.query)
            if 'phone' in query_params:
                phone_numbers.append(query_params['phone'][0])
                social_links['whatsapp'] = link
        for network, pattern in social_networks.items():
            if pattern in link:
                social_links[network] = link

    return title, description, favicon, emails, phone_numbers, social_links, original_response

async def scrape_metadata(url, use_third_party=False):
    # Add https:// if the URL does not start with http or https
    if not url.lower().startswith(('http://', 'https://')):
        url = 'https://' + url

    ua = UserAgent()
    headers = {
        'User-Agent': ua.random
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            if use_third_party:
                result = await fetch_metadata_from_third_party(client, url)
                if result is None:
                    return {'error': 'Failed with third-party API', 'url': url}
                title, description, favicon, emails, phone_numbers, social_links, original_response = result
            else:
                title, description, favicon, emails, phone_numbers, social_links = await fetch_metadata_from_url(client, url, headers)
            original_response = None
        except (RetryError, httpx.HTTPStatusError) as e:
            logger.warning(f"Failed to fetch {url} directly, using third-party API: {str(e)}")
            # Fallback to third-party API if scraping fails
            result = await fetch_metadata_from_third_party(client, url)
            if result is None:
                return {'error': f"Failed with third-party API: {e}", 'url': url}
            title, description, favicon, emails, phone_numbers, social_links, original_response = result

        return {
            'url': url,
            'title': title,
            'description': description,
            'favicon': favicon,
            'emails': emails,
            'phone_numbers': list(set(phone_numbers)),  # Remove duplicates
            'social_links': social_links,
            'original_response': original_response
        }

async def main():
    url = "https://www.sunokrom.com"
    result = await scrape_metadata(url)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
