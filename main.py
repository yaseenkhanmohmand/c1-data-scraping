# import packages
import os
import re
import json
import requests
from bs4 import BeautifulSoup
import time
from google.cloud import storage
from google.oauth2.service_account import Credentials

# Parse the JSON key from the environment variable
credentials_json = json.loads(os.environ.get('gcp-rehab-ai-secret.json'))

# Create credentials object
credentials = Credentials.from_service_account_info(credentials_json)


# Instantiates a client
storage_client = storage.Client()
GCS_PROJECT_ID = "ac215-399020"
GCS_BUCKET_NAME = "rehab-image-detection-data"


# CONSTANTS
# URLS to scrape
FIXER_URL_TO_SCRAPE = 'https://fayar.craigslist.org/search/gravette-ar/rea?hasPic=1&lat=36.4294&lon=-94.4477&min_price=100000&query=fixer%20upper&search_distance=1000#search=1~gallery~0~0'
RENOVATED_URL_TO_SCRAPE = 'https://boston.craigslist.org/search/boston-ma/rea?lat=42.3583&lon=-71.0603&min_price=100000&query=renovated&search_distance=1000#search=1~gallery~0~0'

# Folders to save downloaded images in /replace this with GCS bucket
FIXER_FOLDER = 'fixer/'
RENOVATED_FOLDER = 'renovated/'

# SCRAPING PARAMS
NUM_PAGES_TO_SCRAPE = 4


# method to get image urls
def get_image_urls(url):
    URL = url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
    }

    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Assuming your soup object is named 'soup'
    links = soup.select('li.cl-static-search-result a')

    # Extract the href attribute from each link
    urls = [link['href'] for link in links]

    # returns a list of URLs
    return urls


# Download images and save them in a renovated folder
def download_images(folder, url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
    }

    # Get the folder name
    folder_name = folder+re.search(r'(\d+).html$', url).group(1)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extracting the JavaScript array using regular expression
        script_content = soup.find('script', text=re.compile('var imgList = ')).string
        img_list_str = re.search(r'var imgList = (\[.*?\]);', script_content).group(1)

        # Parsing the extracted JSON string
        img_list = json.loads(img_list_str)

        # Getting all image URLs from the parsed JSON list
        img_urls = [img['url'] for img in img_list]

        # Create directory if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # Download and save each image
        for idx, img_url in enumerate(img_urls, 1):
            img_response = requests.get(img_url, headers=headers)
            img_response.raise_for_status()  # Raise an error for bad responses
            with open(f'{folder_name}/image_{idx}.jpg', 'wb') as file:
                file.write(img_response.content)

            time.sleep(0.1)  # Sleep for 1 second between image downloads

        print("Images downloaded!")

    except requests.RequestException as e:
        print(f"Error encountered: {e}")


# Uploads a file to a GCS bucket
def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")


# main method
def main():

    # initialize empty list to store all image urls
    all_fixer_urls = []
    all_renovated_urls = []

    # for num_pages_to_scrape, get all image urls
    for i in range(NUM_PAGES_TO_SCRAPE):
        all_fixer_urls.extend(get_image_urls(FIXER_URL_TO_SCRAPE))
        all_renovated_urls.extend(get_image_urls(RENOVATED_URL_TO_SCRAPE))
        all_fixer_urls
        all_renovated_urls

    # remove duplicates
    all_fixer_urls = list(set(all_fixer_urls))
    all_renovated_urls = list(set(all_renovated_urls))

    # start downloading fixer images
    i = 0
    for url in all_fixer_urls:
        time.sleep(1)
        download_images(FIXER_FOLDER, url)
        i += 1
        print(i)

    # start downloading renovated images
    i = 0
    for url in all_fixer_urls:
        time.sleep(1)
        download_images(FIXER_FOLDER, url)
        i += 1
        print(i)

    # Upload an image to the "images/" folder
    #upload_blob(GCS_BUCKET_NAME, "local/path/to/image.jpg", "images/image.jpg")

    # Upload a text file to the "text/" folder
    #upload_blob(GCS_BUCKET_NAME, "local/path/to/text.txt", "text/text.txt")


if __name__ == "__main__":
    main()
