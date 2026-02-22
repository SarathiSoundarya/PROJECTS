import os
import requests


DOCUMENT_URLS = {
    # WHO Air Quality Guidelines
    "https://cdn.who.int/media/docs/default-source/who-compendium-on-health-and-environment/who_compendium_chapter2.pdf?sfvrsn=14f84896_8":"WHO_Air_Pollution_Compendium",

    # India Health advisory of Air Pollution
    "https://ncdc.mohfw.gov.in/wp-content/uploads/2024/07/Enclosure-Air-Pollution-Health-Advisory-Oct-2023.pdf":"India_Health_Advisory_Air_Pollution",

    # WHO Climate Change and Health
    "https://apps.who.int/gb/ebwha/pdf_files/WHA77/A77_ACONF7-en.pdf":"WHO_Climate_Change_and_Health",

    # NDMA Heatwave Guidelines
    "https://ndma.gov.in/sites/default/files/PDF/PPTs/TechnicalSession1/01_Kunal_Satyarthi.pdf":"NDMA_Heatwave_Guidelines",

    # NDMA Flood Guidelines
    "https://nidm.gov.in/pdf/guidelines/floods.pdf":"NDMA_Flood_Guidelines",
}

SAVE_DIR = "knowledge_docs"
os.makedirs(SAVE_DIR, exist_ok=True)


def download_files(urls):

    for url in urls.keys():

        filename = DOCUMENT_URLS[url] + ".pdf"

        filepath = os.path.join(SAVE_DIR, filename)

        print("Downloading:", filename)

        response = requests.get(url)

        with open(filepath, "wb") as f:
            f.write(response.content)

    print(" All files downloaded")


download_files(DOCUMENT_URLS)
