import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urlunparse

def extract_ama_episodes(xml_file):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Namespace dictionary
    namespaces = {
        'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        'content': 'http://purl.org/rss/1.0/modules/content/'
    }
    
    # Find all item elements
    for item in root.findall('.//item'):
        title = item.find('title').text
        # Check if title starts with "AMA"
        if title and title.startswith('AMA'):
            enclosure = item.find('enclosure')
            if enclosure is not None:
                # Parse URL and remove query parameters
                parsed_url = urlparse(enclosure.get('url'))
                clean_url = urlunparse(parsed_url._replace(query=''))
                print(f"Title: {title}")
                print(f"URL: {clean_url}\n")

if __name__ == "__main__":
    # Replace 'podcast.xml' with your actual XML file path
    extract_ama_episodes('sean-carrolls-mindscape.xml')
