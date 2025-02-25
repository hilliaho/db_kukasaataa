import typer
from services.hankeikkuna_api_service import HankeikkunaApiService as Hankeikkuna
from services.avoindata_api_service import AvoindataApiService as Avoindata
from services.db_service import DBService
from utils.avoindata import process_and_store_data
from utils.avoindata import process_asiantuntijalausunnot
from utils.formatter import print_pretty_json
from utils.hankeikkuna import process_hankeikkuna_data
from utils.hankeikkuna import find_he_id_from_data
from utils.hankeikkuna import find_proposal_identifier_list
import time


app = typer.Typer(help="Sovellus avoindatan ja hankeikkuna-datan käsittelyyn.")
db_service = DBService()


@app.command(name="eaa")
def export_all_avoindata():
    """Vie kaikki avoindata tietokantaan."""
    per_page = 30
    typer.echo("Haetaan avoindataa...")
    i = 0
    while True:
        typer.echo(f"Haetaan sivulta {i + 1}")
        try:
            avoindata_data = Avoindata.fetch_data_from_api(per_page, i + 1)
            if not avoindata_data:
                typer.echo("Tapahtui virhe. Dataa ei voitu hakea.")
                break
            process_and_store_data(avoindata_data, per_page)
            if not avoindata_data.get("hasMore"):
                typer.echo("Ei enempää dataa haettavana.")
                break
        except Exception as e:
            typer.echo(f"Virhe haettaessa avoindataa: {e}")
            break
        i += 1
    typer.echo("Kaikki avoindata tallennettu tietokantaan.")


@app.command(name="esa")
def export_selected_avoindata(per_page: int, page: int):
    """Vie valittu avoindata tietokantaan.  Käyttö: esa [per_page] [page]"""
    try:
        typer.echo(f"Haetaan avoindata: per_page={per_page}, page={page}")
        avoindata_data = Avoindata.fetch_data_from_api(per_page, page)
        if avoindata_data:
            process_and_store_data(avoindata_data, per_page)
        else:
            typer.echo("Tapahtui virhe. Dataa ei voitu hakea.")
    except Exception as e:
        typer.echo(f"Virhe: {e}")


@app.command(name="eah")
def export_all_hankeikkuna_data():
    """Vie kaikki käsitelty hankeikkuna-data tietokantaan"""
    per_page = 10
    page = 1
    max_pages = 1000
    max_retries = 5
    for page in range(1, max_pages+1):
        typer.echo(f"Haetaan dataa sivulta {page}...")
        retries = 0
        while retries < max_retries:
            try:
                export_selected_hankeikkuna_data(per_page, page)
                break
            except Exception as e:
                retries += 1
                typer.echo(f"Virhe sivulla {page}: {e}. Yritys {retries}/{max_retries}")
                if retries >= max_retries:
                    typer.echo(f"Virhe sivulla {page}, eikä yrityksiä enää jäljellä. Prosessi keskeytetään.")
                    break
                time.sleep(5)

@app.command(name="findh")
def print_he_from_hankeikkuna(he: str):
    """Etsi ja tulosta tietty hanke hankeikkunasta he-tunnuksen perusteella"""
    per_page = 1000
    page = 1
    max_pages = 1000
    max_retries = 5
    for page in range(1, max_pages+1):
        typer.echo(f"Haetaan dataa sivulta {page}...")
        retries = 0
        try:
            hankeikkuna_data = Hankeikkuna.fetch_data_from_api(per_page, page)
            found = find_he_id_from_data(hankeikkuna_data, he)
            if found:
                print_pretty_json(found)
                break
        except Exception as e:
            retries += 1
            typer.echo(f"Virhe sivulla {page}: {e}. Yritys {retries}/{max_retries}")
            if retries >= max_retries:
                typer.echo(f"Virhe sivulla {page}, eikä yrityksiä enää jäljellä. Prosessi keskeytetään.")
                break
            time.sleep(5)

@app.command(name="esh")
def export_selected_hankeikkuna_data(per_page: int, page:int):
    """Vie sivullinen käsiteltyä hankeikkuna-dataa tietokantaan"""
    try:
        typer.echo(f"Haetaan hankeikkuna-dataa...")
        hankeikkuna_data = Hankeikkuna.fetch_data_from_api(per_page, page)
    except Exception as api_error:
        typer.echo(f"Virhe API-kutsussa: {api_error}")
        return
    
    try:
        submission_data = process_hankeikkuna_data(hankeikkuna_data)
    except Exception as processing_error:
        typer.echo(f"Virhe datan käsittelyssä: {processing_error}")
        return
    for i in range(len(submission_data)):
        try:
            preparatory_id = submission_data[i]["preparatoryIdentifier"]
            submissions = submission_data[i]["submissions"]
            he_id = submission_data[i]["proposalIdentifier"]
            modified_count = db_service.update_document(he_id, preparatory_id, submissions)
            if modified_count > 0:
                typer.echo(f"Updated {he_id}")
        except Exception as db_error:
            typer.echo(f"Virhe tietokantaoperaatiossa: ({he_id}){db_error}")
    
@app.command(name="psh")
def print_selected_hankeikkuna_data(per_page: int, page: int):
    """Tulosta sivullinen käsiteltyä hankeikkuna-dataa"""
    try:
        hankeikkuna_data = Hankeikkuna.fetch_data_from_api(per_page, page)
    except Exception as e:
        typer.echo(f"Virhe haettaessa dataa: {e}")
    processed_data = process_hankeikkuna_data(hankeikkuna_data)
    print_pretty_json(processed_data)
    typer.echo(f"Processed data size: {len(processed_data)}")



@app.command(name="pa")
def print_avoindata(per_page: int, page: int):
    """Tulosta avoindataa rajapinnasta. Käyttö: pa [per_page] [page]"""
    try:
        avoindata_data = Avoindata.fetch_data_from_api(per_page, page)
        print_pretty_json(avoindata_data)
    except Exception as e:
        typer.echo(f"Virhe haettaessa dataa: {e}")


@app.command(name="ph")
def print_hankeikkuna_data(per_page: int, page: int):
    """Tulosta hankeikkuna-dataa rajapinnasta. Käyttö: ph [per_page] [page]"""
    try:
        hankeikkuna_data = Hankeikkuna.fetch_data_from_api(per_page, page)
        print_pretty_json(hankeikkuna_data["result"])
    except Exception as e:
        typer.echo(f"Virhe haettaessa dataa: {e}")


@app.command(name="phh")
def print_hankeikkuna_headers():
    try:
        hankeikkuna_data = Hankeikkuna.fetch_data_from_api(1, 1)
        for key in hankeikkuna_data["result"][0].keys():
            print_pretty_json(key)
    except Exception as api_error:
        typer.echo(f"Virhe haettaessa dataa: {api_error}")

@app.command(name="ak")
def print_hankeikkuna_asiakirjat():
    try:
        hankeikkuna_data = Hankeikkuna.fetch_data_from_api(1000, 1)
        for i in range(10):
           for asiakirja in hankeikkuna_data["result"][i]["asiakirjat"]:
                print_pretty_json(asiakirja["nimi"]["fi"])
    except Exception as api_error:
        typer.echo(f"Virhe haettaessa dataa: {api_error}")


@app.command(name="find")
def find_document_by_he_id(he_id):
    """Etsi hanke omasta tietokannasta he-tunnuksen perusteella"""
    try:
        document = db_service.find_document_by_he_id(he_id)
        if document:
            name = document["name"]
            typer.echo(f"{he_id}: {name}")
            typer.echo(f"Sisältää kentät: {list(document.keys())}")
        else:
            typer.echo(f"Dokumenttia tunnuksella {he_id} ei löytynyt tietokannasta.")
    except Exception as db_error:
        typer.echo("Virhe tietokantaoperaatiossa: {db_error}")

@app.command(name="phe")
def print_he_lists_from_hankeikkuna(per_page: int, page: int):
    """Tulosta he-numerot sivullisesta hankeikkuna-dataa"""
    try:
        hankeikkuna_data = Hankeikkuna.fetch_data_from_api(per_page, page)
    except Exception as e:
        typer.echo(f"Virhe haettaessa dataa: {e}")
    for i in range(per_page):
        processed_data = find_proposal_identifier_list(hankeikkuna_data, i)
        print_pretty_json(processed_data)

@app.command(name="rep")
def remove_empty_proposals():
    """Poista tyhjät hallituksen esitykset tietokannasta"""
    try:
        db_service.translate_to_finnish()
    except Exception as db_error:
        typer.echo(f"Virhe tietokantaoperaatiossa: {db_error}")

@app.command(name="vp")
def clean_all_he_id_in_database():
    try:
        db_service.clean_identifiers()
    except Exception as db_error:
        typer.echo(f"Virhe tietokantaoperaatiossa: {db_error}")

@app.command(name="index")
def create_search_index():
    try:
        db_service.create_search_index()
    except Exception as db_error:
        typer.echo(f"Virhe hakuindeksin luomisessa: {db_error}")

@app.command(name="doc")
def add_document_key_to_db():
    try:
        db_service.add_document_field()
    except Exception as db_error:
        typer.echo(f"Virhe dokumenttikentän luomisessa: {db_error}")

@app.command(name="eal")
def export_asiantuntijalausunnot_from_api_to_db():
    """Hae kaikki asiantuntijalausunnot avoindatasta ja vie ne tietokantaan"""
    i = 0
    while True:
        typer.echo(f"Haetaan asiantuntijalausuntoja sivulta {i}")
        api_data = Avoindata.fetch_asiantuntijalausunnot_from_api(100, i)
        has_more = api_data["hasMore"]
        data = process_asiantuntijalausunnot(api_data)
        for element in data:
            he_id = element["he_tunnus"]
            db_service.export_asiantuntijalausunnot(element, he_id)
        print(i)
        if not has_more:
            break
        i +=1



if __name__ == "__main__":
    app()
