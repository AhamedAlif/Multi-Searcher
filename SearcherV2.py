import asyncio
import aiohttp
from bs4 import BeautifulSoup
from tqdm import tqdm
import os
import random
import logging
grn = "\x1b[38;5;46m"
BASE_URLS = {
    "bing": "http://www.bing.com/search",
    "duckduckgo": "https://duckduckgo.com/html?q={query}",
    "yahoo": "https://search.yahoo.com/search?p={query}",
}

async def fetch_batch_urls(session, query, base_url, start, max_results, batch_size, pbar, user_agent):
    headers = {
        "User-Agent": user_agent
    }

    unique_urls = set()
    semaphore = asyncio.Semaphore(5)  # Adjust the concurrency level as needed

    while len(unique_urls) < max_results:
        params = {
            "q" if base_url == BASE_URLS["bing"] else "": query,
            "first" if base_url == BASE_URLS["bing"] else "": start
        }

        try:
            async with semaphore, session.get(base_url.format(query=query), params=params, headers=headers, timeout=10) as response:
                response.raise_for_status()

                soup = BeautifulSoup(await response.text(), 'html.parser')
                current_urls = [a['href'] for a in soup.find_all('a', href=True) if 'http' in a['href']]
                unique_urls.update(current_urls)

                start += batch_size
                if not current_urls:
                    break

        except aiohttp.ClientError as e:
            logging.error(f"Error during the request: {e}")
            break

        pbar.update(len(current_urls))
        await asyncio.sleep(0.1)

    return list(unique_urls)[:max_results]

async def search_bing_and_duckduckgo_and_yahoo(query, max_results=500, batch_size=10):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
    ]

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=5)) as session:
        tasks = [
            fetch_batch_urls(session, query, BASE_URLS["bing"], 0, max_results, batch_size, tqdm(total=max_results, desc=f"Fetching URLs from Bing", unit="URL", dynamic_ncols=True), random.choice(user_agents)),
            fetch_batch_urls(session, query, BASE_URLS["duckduckgo"], 0, max_results, batch_size, tqdm(total=max_results, desc=f"Fetching URLs from DuckDuckGo", unit="URL", dynamic_ncols=True), random.choice(user_agents)),
            fetch_batch_urls(session, query, BASE_URLS["yahoo"], 0, max_results, batch_size, tqdm(total=max_results, desc=f"Fetching URLs from Yahoo", unit="URL", dynamic_ncols=True), random.choice(user_agents)),
        ]

        bing_results, duckduckgo_results, yahoo_results = await asyncio.gather(*tasks)

    combined_results = set(bing_results).union(duckduckgo_results).union(yahoo_results)

    return combined_results

async def process_queries_from_file(file_path, max_results_per_query=100):
    with open(file_path, 'r') as file:
        queries = [line.strip() for line in file if line.strip()]

    for query in queries:
        print(f"Searching for '{query}'...")
        results = await search_bing_and_duckduckgo_and_yahoo(query, max_results=max_results_per_query)
        
        result_file_path = f"search_results_{query.replace(' ', '_')}.txt"
        with open(result_file_path, 'w') as result_file:
            result_file.write(f"Total {len(results)} unique URLs found for '{query}' from all search engines:\n")
            for url in results:
                result_file.write(url + '\n')

        print(f"Results saved in {result_file_path}\n")

if __name__ == "__main__":
    try:
        logo = f"""{grn}

╔╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╤╗
╟┼┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┼╢
╟┤ ███▄ ▄███▓ █    ██  ██▓  ▄▄▄█████▓ ██▓     ██████ ▓█████ ▄▄▄       ██▀███   ▄████▄   ██░ ██ ▓█████  ██▀███  ├╢
╟┤▓██▒▀█▀ ██▒ ██  ▓██▒▓██▒  ▓  ██▒ ▓▒▓██▒   ▒██    ▒ ▓█   ▀▒████▄    ▓██ ▒ ██▒▒██▀ ▀█  ▓██░ ██▒▓█   ▀ ▓██ ▒ ██▒├╢
╟┤▓██    ▓██░▓██  ▒██░▒██░  ▒ ▓██░ ▒░▒██▒   ░ ▓██▄   ▒███  ▒██  ▀█▄  ▓██ ░▄█ ▒▒▓█    ▄ ▒██▀▀██░▒███   ▓██ ░▄█ ▒├╢
╟┤▒██    ▒██ ▓▓█  ░██░▒██░  ░ ▓██▓ ░ ░██░     ▒   ██▒▒▓█  ▄░██▄▄▄▄██ ▒██▀▀█▄  ▒▓▓▄ ▄██▒░▓█ ░██ ▒▓█  ▄ ▒██▀▀█▄  ├╢
╟┤▒██▒   ░██▒▒▒█████▓ ░██████▒▒██▒ ░ ░██░   ▒██████▒▒░▒████▒▓█   ▓██▒░██▓ ▒██▒▒ ▓███▀ ░░▓█▒░██▓░▒████▒░██▓ ▒██▒├╢
╟┤░ ▒░   ░  ░░▒▓▒ ▒ ▒ ░ ▒░▓  ░▒ ░░   ░▓     ▒ ▒▓▒ ▒ ░░░ ▒░ ░▒▒   ▓▒█░░ ▒▓ ░▒▓░░ ░▒ ▒  ░ ▒ ░░▒░▒░░ ▒░ ░░ ▒▓ ░▒▓░├╢
╟┤░  ░      ░░░▒░ ░ ░ ░ ░ ▒  ░  ░     ▒ ░   ░ ░▒  ░ ░ ░ ░  ░ ▒   ▒▒ ░  ░▒ ░ ▒░  ░  ▒    ▒ ░▒░ ░ ░ ░  ░  ░▒ ░ ▒░├╢
╟┤░      ░    ░░░ ░ ░   ░ ░   ░       ▒ ░   ░  ░  ░     ░    ░   ▒     ░░   ░ ░         ░  ░░ ░   ░     ░░   ░ ├╢
╟┤       ░      ░         ░  ░        ░           ░     ░  ░     ░  ░   ░     ░ ░       ░  ░  ░   ░  ░   ░     ├╢
╟┤ Tool By : Ahamed Alif | Version : 1.0                                      ░                                ├╢
╟┼┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┼╢
╚╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╧╝

 
          """ 
        print(logo)
        dork_file_path = input("Enter the path to the dork text file: ")
        max_results_per_query = 100

        asyncio.run(process_queries_from_file(dork_file_path, max_results_per_query))

    except KeyboardInterrupt:
        print("\nSearch process interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")