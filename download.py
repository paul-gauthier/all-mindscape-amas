#!/usr/bin/env python3

import json
import os
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from xml.etree import ElementTree as ET

import requests
from tqdm import tqdm

from ama_extractor import extract_ama_episodes


def get_ama_episodes(xml_file):
    """Get AMA episodes with their titles and URLs"""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    namespaces = {
        "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }

    episodes = []
    for item in root.findall(".//item"):
        title = item.find("title").text
        if title and title.startswith("AMA"):
            pub_date = item.find("pubDate").text
            enclosure = item.find("enclosure")
            if enclosure is not None:
                parsed_url = urlparse(enclosure.get("url"))
                clean_url = urlunparse(parsed_url._replace(query=""))
                episodes.append({"title": title, "url": clean_url, "date": pub_date})
    return episodes


def download_episode(url, filename):
    """Download an episode and save it to filename. Returns final URL if successful."""
    print(f"Downloading from URL: {url}")

    if os.path.exists(filename):
        print(f"File {filename} already exists - skipping")
        return False, None

    temp_filename = f"{filename}.download"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        try:
            # Get total file size from headers
            total_size = int(response.headers.get("content-length", 0))

            with open(temp_filename, "wb") as f:
                with tqdm(
                    total=total_size,
                    unit="iB",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=f"Downloading {os.path.basename(filename)}",
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        size = f.write(chunk)
                        pbar.update(size)

            # Atomic rename on success
            os.rename(temp_filename, filename)
            return True, response.url
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            print(f"Error downloading {filename}: {str(e)}")
            return False, None
    return False, None


def format_filename(date_str, title):
    """Format filename as YYYY-MM-AMA.mp3"""
    try:
        # Parse date from format like "Wed, 03 Jan 2024 10:00:00 +0000"
        dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        return f"data/{dt.strftime('%Y-%m')}-AMA.mp3"
    except ValueError:
        return None


def main():
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    xml_file = "sean-carrolls-mindscape.xml"
    episodes = get_ama_episodes(xml_file)

    for episode in episodes:
        filename = format_filename(episode["date"], episode["title"])
        if filename:
            # Create JSON filename based on MP3 filename
            json_filename = os.path.splitext(filename)[0] + ".json"

            # Get existing final_url if file exists
            final_url = None
            if os.path.exists(filename):
                print(f"Skipping {episode['title']} - already exists at {filename}")
                if os.path.exists(json_filename):
                    with open(json_filename) as f:
                        existing_metadata = json.load(f)
                        final_url = existing_metadata.get("final_url")
            else:
                print(f"Downloading {episode['title']} to {filename}")
                success, final_url = download_episode(episode["url"], filename)
                if success:
                    print(f"Successfully saved {filename}")
                else:
                    print(f"Failed to download {filename}")

            # Save metadata for this episode immediately
            episode_meta = {
                "filename": filename,
                "url": episode["url"],
                "final_url": final_url,
                "title": episode["title"],
                "date": episode["date"],
            }

            with open(json_filename, "w") as f:
                json.dump(episode_meta, f, indent=2)
            print(f"Saved episode metadata to {json_filename}")
        else:
            print(f"Could not parse date for {episode['title']}")


if __name__ == "__main__":
    main()
