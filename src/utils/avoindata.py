import pdfplumber
import requests
import re
import xml.etree.ElementTree as ET
from services.db_service import DBService

db_service = DBService()

def process_preparatory_documents(api_data):
    """Käsittele valmisteluasiakirjat ja muokkaa ne sopivaan muotoon"""
    result_list = api_data["rowData"]
    processed_list = []
    for i in range(len(result_list)):
        identifier = result_list[i][1]
        identifier = remove_vp(identifier)
        xml_name = result_list[i][3]
        xml_doc_type = result_list[i][4]
        xml_url = result_list[i][5]
        name_row = parse_xml_name(xml_name)
        doc_type = parse_xml_doc_type(xml_doc_type)
        name = remove_unnecessary_info_from_name(name_row)
        url_match = re.search(r'href="([^"]+)"', xml_url)
        url = ""
        if url_match:
            url = url_match.group(1)
        processed_element = {
            "he_tunnus": identifier,
            "asiakirjatyyppi": doc_type,
            "nimi": name,
            "url": url
        }
        processed_list.append(processed_element)
    return processed_list

def remove_vp(he_id):
    he_id = he_id.split(",")[0]
    return re.sub(r'\s*vp$', '', he_id)

def remove_unnecessary_info_from_name(text):
    text = text.strip()
    name = re.sub(r'^[A-Z]+\s\d{1,3}/\d{4}\svp\s[A-Za-z]+\s\d{2}\.\d{2}\.\d{4}\s', '', text)
    name = re.sub(r'\s*Asiantuntijalausunto$', '', name)
    return name

def process_and_store_data(api_data, per_page):
    """Käsittelee ja tallentaa datan tietokantaan."""
    government_proposals = parse_government_proposals(api_data, per_page)
    for proposal in government_proposals:
        if not db_service.document_exists(proposal["id"]):
            db_service.add_document(proposal)
            print(f"Lisätty dokumentti {proposal['id']} tietokantaan")
        else:
            print(f"Dokumentti {proposal['id']} on jo tietokannassa")


def parse_government_proposals(data, per_page):
    government_proposals = []
    for i in range(per_page):
        id = data["rowData"][i][0]
        he_identifier = data["rowData"][i][1]
        xml_name = data["rowData"][i][3]
        proposal_url = data["rowData"][i][5]
        name = parse_xml_name(xml_name)
        url_match = re.search(r'href="([^"]+)"', proposal_url)
        if url_match:
            proposal_url = url_match.group(1)
        if name and re.match(r"^HE \d{1,3}/\d{4} vp$", he_identifier):
            document = create_document(
                id,
                he_identifier,
                name,
                proposal_url,
            )
            government_proposals.append(document)
    return government_proposals


def parse_xml_name(xml_data):
    wrapped_xml = f"<root>{xml_data}</root>"

    try:
        root = ET.fromstring(wrapped_xml)
        names = root.findall(
            ".//{http://www.vn.fi/skeemat/metatietoelementit/2010/04/27}NimekeTeksti"
        )
        name = names[0]
        return name.text
    except ET.ParseError as e:
        print(f"XML-parsinta epäonnistui: {e}")
        return None

def parse_xml_doc_type(xml_data):
    wrapped_xml = f"<root>{xml_data}</root>"

    try:
        root = ET.fromstring(wrapped_xml)
        names = root.findall(
            ".//{http://www.vn.fi/skeemat/metatietoelementit/2010/04/27}AsiakirjatyyppiNimi"
        )
        name = names[0]
        return name.text
    except ET.ParseError as e:
        print(f"XML-parsinta epäonnistui: {e}")
        return None


def extract_text_from_pdf(pdf_url):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        temp_pdf_path = "temp.pdf"
        with open(temp_pdf_path, "wb") as f:
            f.write(response.content)
        text = ""
        with pdfplumber.open(temp_pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
        return text
    else:
        print(f"Failed to fetch PDF: {response.status_code}")
        return None


def find_preparatory_identifier(text):
    pattern = r"[A-Z]{2,3}\d{3}:\d{2}/\d{4}"
    matches = re.findall(pattern, text)
    print(f"Matches found: {matches}")
    return matches if matches else None


def create_document(
    id, he_identifier, name, proposal_url, proposal_content, preparatory_identifier
):
    return {
        "id": id,
        "heIdentifier": he_identifier,
        "name": name,
        "proposalUrl": proposal_url,
        "proposalContent": proposal_content,
        "preparatoryIdentifier": preparatory_identifier,
    }
