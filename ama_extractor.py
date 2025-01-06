import xml.etree.ElementTree as ET

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
                url = enclosure.get('url')
                print(f"Title: {title}")
                print(f"URL: {url}\n")

if __name__ == "__main__":
    # Replace 'podcast.xml' with your actual XML file path
    extract_ama_episodes('podcast.xml')
