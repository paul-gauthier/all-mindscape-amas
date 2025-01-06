#!/usr/bin/env python3

import os
import requests
from datetime import datetime
from ama_extractor import extract_ama_episodes
from xml.etree import ElementTree as ET
from urllib.parse import urlparse, urlunparse

def get_ama_episodes(xml_file):
    """Get AMA episodes with their titles and URLs"""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    namespaces = {
        'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        'content': 'http://purl.org/rss/1.0/modules/content/'
    }

    episodes = []
    for item in root.findall('.//item'):
        title = item.find('title').text
        if title and title.startswith('AMA'):
            pub_date = item.find('pubDate').text
            enclosure = item.find('enclosure')
            if enclosure is not None:
                parsed_url = urlparse(enclosure.get('url'))
                clean_url = urlunparse(parsed_url._replace(query=''))
                episodes.append({
                    'title': title,
                    'url': clean_url,
                    'date': pub_date
                })
    return episodes

def download_episode(url, filename):
    """Download an episode and save it to filename"""
    if os.path.exists(filename):
        print(f"File {filename} already exists - skipping")
        return False

    temp_filename = f"{filename}.download"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        try:
            with open(temp_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            # Atomic rename on success
            os.rename(temp_filename, filename)
            return True
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            print(f"Error downloading {filename}: {str(e)}")
            return False
    return False

def format_filename(date_str, title):
    """Format filename as YYYY-MM-AMA.mp3"""
    try:
        # Parse date from format like "Wed, 03 Jan 2024 10:00:00 +0000"
        dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        return f"data/{dt.strftime('%Y-%m')}-AMA.mp3"
    except ValueError:
        return None

def main():
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)

    xml_file = 'sean-carrolls-mindscape.xml'
    episodes = get_ama_episodes(xml_file)

    for episode in episodes:
        filename = format_filename(episode['date'], episode['title'])
        if filename:
            if os.path.exists(filename):
                print(f"Skipping {episode['title']} - already exists at {filename}")
                continue

            print(f"Downloading {episode['title']} to {filename}")
            if download_episode(episode['url'], filename):
                print(f"Successfully saved {filename}")
            else:
                print(f"Failed to download {filename}")
        else:
            print(f"Could not parse date for {episode['title']}")

if __name__ == "__main__":
    main()
