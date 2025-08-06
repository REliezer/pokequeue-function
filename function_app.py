import io
import os
import azure.functions as func
import datetime
import json
import logging
import requests
import random
from dotenv import load_dotenv
import pandas as pd
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()
load_dotenv()

logging.basicConfig( level=logging.INFO )
logger = logging.getLogger(__name__)

DOMAIN = os.getenv("DOMAIN")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")
STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")

@app.queue_trigger(
    arg_name="azqueue", 
    queue_name="requests", 
    connection="QueueAzureWebJobsStorage"
)
def QueueTriggerPokeReport(azqueue: func.QueueMessage):
    id = None
    try:
        body = azqueue.get_body().decode('utf-8')
        logger.info(f'Body Queue: {body}')
        record = json.loads(body)

        id = record["id"]
        sample_size = record.get('sample_size')
        update_request( id , "inprogress" )

        request_info = get_request(id)
        if sample_size is not None:            
            pokemons = get_pokemons( request_info[0]["type"], sample_size )
        else:
            pokemons = get_pokemons( request_info[0]["type"] )

        if not pokemons:
            logger.error(f"No se encontraron Pokémon para el tipo '{request_info[0]["type"]}'. Marcando como failed.")
            update_request(id, "failed")
            return
        
        pokemon_bytes = generate_csv_to_blob( pokemons )
        blob_name = f"poke_report_{id}.csv"
        upload_csv_to_blob( blob_name=blob_name, csv_data=pokemon_bytes )
        logger.info( f"Archivo {blob_name} se subio con exito" )

        url_completa = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{BLOB_CONTAINER_NAME}/{blob_name}"
        
        update_request( id , "completed", url_completa )
    except Exception as e:
        logger.error(f"Ha ocurrido un error irrecuperable procesando la solicitud. ID: {id}. Error: {e}")
        if id:
            update_request(id, "failed")
        raise    

def update_request( id: int, status: str, url: str = None ) -> dict:
    payload = {
        "status": status,
        "id": id
    }
    if url:
        payload["url"] = url

    response = requests.put( f"{DOMAIN}/api/request" , json=payload )
    return response.json()

def get_request(id: int) -> dict:
    response = requests.get( f"{DOMAIN}/api/request/{id}"  )
    return response.json()

def get_pokemons( type: str, sample_size: int = None ) -> dict:
    try:
        pokeapi_url = f"https://pokeapi.co/api/v2/type/{type}"
        response = requests.get(pokeapi_url, timeout=60)
        response.raise_for_status()
        data = response.json()
        pokemon_entries = data.get('pokemon', [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener datos del tipo {type}: {e}")
        return []

    all_pokemon_data = []
    total_pokemon = sample_size if sample_size is not None else len(pokemon_entries)
    pokemon_collection = random.sample(pokemon_entries, k=sample_size) if (sample_size is not None and sample_size < len(pokemon_entries)) else pokemon_entries
    
    logger.info(f"Procesando {total_pokemon} Pokemon del tipo {type}")

    for pokemon in pokemon_collection:
        pokemon_dict = {
            'name': pokemon['pokemon']['name'],
            'url': pokemon['pokemon']['url']
        }
        url = pokemon['pokemon']['url']

        #Recorremos la URL
        pokemon_info = get_pokemon_info(url)
        pokemon_dict.update(pokemon_info)

        all_pokemon_data.append(pokemon_dict)
    logger.info(f"Completado: obtenidos datos de {len(all_pokemon_data)} de {total_pokemon} Pokemon {type}")
    return all_pokemon_data

def get_pokemon_info(url: str) -> list:
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        data_pokemon = response.json()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error al obtener datos del Pokemon: {e}")
    except Exception as e:
        logger.warning(f"Error inesperado procesando Pokemon: {e}")

    #info basica
    height = data_pokemon.get('height')
    weight = data_pokemon.get('weight')
    #types
    data_types = data_pokemon.get('types', [])
    data_types_type_name = [item.get('type', {}).get('name') for item in data_types if isinstance(item, dict)]
    #stats
    data_stats = data_pokemon.get('stats', [])
    data_stats_stat_name = [item.get('stat', {}).get('name') for item in data_stats if isinstance(item, dict)]
    data_stats_stat_base = [item.get('base_stat') for item in data_stats if isinstance(item, dict)]
    stats_dict = {data_stats_stat_name[i]: data_stats_stat_base[i] for i in range(len(data_stats_stat_name))}
    #abilities
    data_abilities = data_pokemon.get('abilities', [])
    data_abilities_ability_name = [item.get('ability', {}).get('name') for item in data_abilities if isinstance(item, dict)]

    pokemon_dict = ({
        'height (dm)': height,
        'weight (hg)': weight,
        'sprite': data_pokemon.get('sprites', {}).get('front_default'),
        'generation': get_pokemon_generation(data_pokemon.get('species', {}).get('url')),
        'types': ", ".join(data_types_type_name)
    })        
    pokemon_dict.update(stats_dict)        
    pokemon_dict.update({
        'abilities': ", ".join(data_abilities_ability_name)
    })

    return pokemon_dict

def get_pokemon_generation(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data.get('generation', {}).get('name') or ''
    
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error al obtener generación desde {url}: {e}")
        return ''
    except Exception as e:
        logger.warning(f"Error inesperado obteniendo generación: {e}")
        return ''

def generate_csv_to_blob( pokemon_list: list ) -> bytes:
    df = pd.DataFrame( pokemon_list )
    output = io.StringIO()
    df.to_csv( output , index=False, encoding='utf-8' )
    csv_bytes = output.getvalue().encode('utf-8')
    output.close()
    return csv_bytes

def upload_csv_to_blob( blob_name: str, csv_data: bytes ):
    try:
        blob_service_client = BlobServiceClient.from_connection_string( AZURE_STORAGE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client( container = BLOB_CONTAINER_NAME, blob=blob_name )
        blob_client.upload_blob( csv_data , overwrite=True )
    except Exception as e:
        logger.error(f"Error al subir el archivo {e} ")
        raise