import asyncio
import json
import sys

from app.scraper.scraper import scrape_metadata

async def main(args):
    # print('*** Scraper test ***')
    # get args from command line, if not exist print help
    if len(args) < 2:
        print('Usage: python main.py <url>')
        sys.exit(1)

    url = args[1]

    response = await scrape_metadata(url)

    # print resonse formatted for better readability dict -> json
    print(json.dumps(response, indent=4))

    # transform response to json and print it formatted
    # print(json.dumps(response, indent=4))



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python main.py <url>')
        sys.exit(1)

    asyncio.run(main(sys.argv))
