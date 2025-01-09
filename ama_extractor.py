#!/usr/bin/env python3
"""
AMA Episode Extractor

This script processes podcast RSS feed XML files to extract information about
'AMA' (Ask Me Anything) episodes. It identifies episodes with titles starting
with 'AMA', extracts their download URLs, and cleans the URLs by removing any
query parameters.

The script is specifically designed to work with Sean Carroll's Mindscape
podcast RSS feed format, but can be adapted for other podcast feeds with
similar XML structure.
"""

import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urlunparse


def extract_ama_episodes(xml_file):
    """
    Extract and display AMA episode information from a podcast RSS feed XML file.

    Args:
        xml_file (str): Path to the XML file containing the podcast RSS feed

    The function:
    1. Parses the XML file using ElementTree
    2. Identifies episodes with titles starting with 'AMA'
    3. Extracts and cleans the episode download URLs
    4. Prints the title and cleaned URL for each AMA episode
    """
    # Parse the XML file using ElementTree
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Define XML namespaces used in podcast RSS feeds
    namespaces = {
        "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",  # iTunes namespace
        "content": "http://purl.org/rss/1.0/modules/content/",  # Content namespace
    }

    # Find all <item> elements in the XML, which represent individual podcast episodes
    for item in root.findall(".//item"):
        title = item.find("title").text
        # Only process episodes with titles starting with "AMA"
        if title and title.startswith("AMA"):
            enclosure = item.find("enclosure")
            if enclosure is not None:
                # Parse the URL and clean it by removing any query parameters
                parsed_url = urlparse(enclosure.get("url"))
                clean_url = urlunparse(parsed_url._replace(query=""))
                # Output the episode information
                print(f"Title: {title}")
                print(f"URL: {clean_url}\n")


if __name__ == "__main__":
    """
    Main execution block. Runs the extractor with a default XML file name.
    Replace 'sean-carrolls-mindscape.xml' with your actual XML file path.
    """
    extract_ama_episodes("sean-carrolls-mindscape.xml")
