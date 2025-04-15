from googleapiclient.discovery import build
from google.cloud import firestore
from dotenv import load_dotenv
import pytz
import os
import re
import time
import logging
import datetime

# Configurações
debug = False
debug_time = 3

data_collection = "playlist_data"
status_collection = "status"
status_document = "playlist_status"

TIMEZONE = pytz.timezone("America/Sao_Paulo")
TODAY_STRING = ""

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(message)s',
        handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def message(text, forced=False):
    if debug or forced:
        logger.info(text)
        time.sleep(debug_time)
    return text

def load_keys():
    
    load_dotenv()
    playlist_id = os.getenv('PLAYLIST_ID')
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    firebase_credentials = os.getenv('FIREBASE_CREDENTIALS')

    return playlist_id, youtube_api_key, firebase_credentials

def set_environment(firebase_credentials):
    if os.path.exists(firebase_credentials):
        message(f"Credenciais encontradas em '{firebase_credentials}'.")
    else:
        message(f"Não foi possível obter credenciais de autenticação do firebase em '{firebase_credentials}', tentando localmente...")
        firebase_credentials = "config/firebase.json"
        if os.path.exists(firebase_credentials):
            message(f"Credenciais encontradas em '{firebase_credentials}'.")
        else:
            return message(f"Não foi possível obter credenciais de autenticação do firebase em '{firebase_credentials}'."), 0

    return firebase_credentials, 1

def set_day():
    global TODAY_STRING
    today = datetime.datetime.now(TIMEZONE)
    TODAY_STRING = today.strftime('%Y-%m-%d')

def init_firestore(firebase_credentials):
    message("Conectando ao Firestore...")
    load_db = firestore.Client.from_service_account_json(firebase_credentials)

    message("Conexão ao Firestore estabelecida.")
    return load_db

def check_data(db):
    # data = -1: Erro
    # data = 0: Não tem dados hoje
    # data = 1: Já tem dados hoje

    message("Verificando se há dados existentes...")
    try:
        doc_ref = db.collection(data_collection).document(TODAY_STRING)
        doc = doc_ref.get()
        if not doc.exists:  # Não há dados no dia atual
            return message("Dados ainda não inseridos no banco."), 0
        return message(f"Dados para {TODAY_STRING} já existem no Firestore."), 1
    except Exception as e:
        return message(f"Ocorreu um erro ao verificar os dados: {str(e)}"), -1

def authenticate_youtube(youtube_api_key):
    message("Autenticando conta da API...")

    try:
        authentication = build("youtube", "v3", developerKey=youtube_api_key)
        return authentication, message("Autenticação concluída."), 1
    except Exception as e:
        return None, message(f"Erro na autenticação: {e}"), 0

def get_data(youtube_authentication, playlist_id):
    message(f"Obtendo dados da playlist '{playlist_id}'...")

    video_count = None
    total_minutes = None

    try:
        request = youtube_authentication.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50
        )
        video_ids = []
        while request:
            response = request.execute()
            video_ids.extend(item["contentDetails"]["videoId"] for item in response["items"])
            request = youtube_authentication.playlistItems().list_next(request, response)

        video_count = len(video_ids)
        total_minutes = 0

        if video_ids:
            for i in range(0, len(video_ids), 50):
                video_request = youtube_authentication.videos().list(
                    part="contentDetails",
                    id=','.join(video_ids[i:i + 50])
                )
                video_response = video_request.execute()
                for video in video_response["items"]:
                    duration = video["contentDetails"]["duration"]
                    total_minutes += parse_duration_to_minutes(duration)

        data_fetched_message = message(f"Playlist contém {video_count} vídeos e {total_minutes} minutos no total.")
        data_fetched = 1

    except Exception as e:
        data_fetched_message = message(f"Ocorreu um erro ao buscar os dados: {str(e)}")
        data_fetched = 0

    return data_fetched, data_fetched_message, video_count, total_minutes

def parse_duration_to_minutes(duration):
    # Regex para extrair os componentes de tempo do formato ISO 8601
    pattern = r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, duration)

    if not match:
        raise ValueError("Formato de duração inválido")

    days = int(match.group(1)) if match.group(1) else 0
    hours = int(match.group(2)) if match.group(2) else 0
    minutes = int(match.group(3)) if match.group(3) else 0
    seconds = int(match.group(4)) if match.group(4) else 0

    # Converte para minutos
    total_minutes = days * 1440 + hours * 60 + minutes + seconds // 60
    return total_minutes

def upload_data(db, video_count, total_minutes):
    message(f"Salvando dados para {TODAY_STRING}: {video_count} vídeos, {total_minutes} minutos...")

    try:
        doc_ref = db.collection(data_collection).document(TODAY_STRING)
        doc_ref.set({
            "video_count": video_count,
            "total_minutes": total_minutes
        }, merge=True)
        return message("Dados salvos com sucesso.", True), 1
    except Exception as e:
        return message(f"Ocorreu um erro ao salvar os dados: {str(e)}", True), 0

def upload_status(db, title, status):
    message(f"Fazendo upload do status {title} no Firestore...")

    try:
        last_title = title + "_timestamp"

        doc_ref = db.collection(status_collection).document(status_document)
        doc_ref.set({
            title: status,
            last_title: datetime.datetime.now(TIMEZONE).isoformat()
        }, merge=True)

        message(f"Status {title} salvo.")

    except Exception as e:
        message(f"Ocorreu um erro ao fazer upload do status: {str(e)}")

# Função principal
def main():

    message("\n\nIniciando salvamento de dados...", True)

    # Inicializa data do dia atual
    set_day()

    playlist_id, youtube_api_key, firebase_credentials = load_keys()

    # Definir ambiente
    firebase_credentials, return_environment = set_environment(firebase_credentials)
    if return_environment == 0:
        return message("Execução finalizada com falha.", True)

    # Faz a conexão com o firebase
    db = init_firestore(firebase_credentials)
    if not db: return message("Execução finalizada com falha.", True)

    # Checa no firebase se já tem dados para hoje
    return_check_data_message, return_check_data_status = check_data(db)
    if return_check_data_status == -1:
        upload_status(db, "final_result", return_check_data_message)
        return message("Execução finalizada com falha.", True)
    if return_check_data_status == 1:
        upload_status(db, "final_result", return_check_data_message)
        return message("Execução finalizada com sucesso.", True)

    # Autentica as credenciais do youtube
    youtube_authentication, return_authentication_message, return_authentication = authenticate_youtube(youtube_api_key)
    if return_authentication == 0:
        upload_status(db, "final_result", return_authentication_message)
        return message("Execução finalizada com falha.", True)

    # Coleta os dados de playlist
    data_fetched, data_fetched_message, video_count, total_minutes = get_data(youtube_authentication, playlist_id)
    if data_fetched == 0:
        upload_status(db, "final_result", data_fetched_message)
        return message("Execução finalizada com falha.", True)

    # Salva os dados no firebase
    return_upload_data_message, return_upload_data_status = upload_data(db, video_count, total_minutes)
    if return_upload_data_status == 0:
        upload_status(db, "final_result", return_upload_data_message)
        return message("Execução finalizada com falha.", True)

    # Salva o status de resultado final no firebase
    upload_status(db, "final_result", return_upload_data_message)
    message("Execução finalizada com sucesso.", True)

if __name__ == "__main__":
    main()