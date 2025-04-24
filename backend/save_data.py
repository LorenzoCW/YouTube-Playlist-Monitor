from googleapiclient.discovery import build
from dotenv import load_dotenv
from google.cloud import firestore
import pytz
import os
import re
import time
import logging
import datetime

# Configurações
debug = True
debug_time = 1

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
    if debug:
        time.sleep(debug_time)
    return text


# -- init --
def set_day():
    message("Definindo data atual...")
    global TODAY_STRING
    today = datetime.datetime.now(TIMEZONE)
    TODAY_STRING = today.strftime('%Y-%m-%d')

def load_keys():
    message("Carregando variáveis secretas...")
    
    load_dotenv()
    playlist_id = os.getenv('PLAYLIST_ID')
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    firebase_credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')

    return playlist_id, youtube_api_key, firebase_credentials_path

def set_environment(firebase_credentials_path):
    if os.path.exists(firebase_credentials_path):
        message(f"Credenciais encontradas em '{firebase_credentials_path}'.")
    else:
        message(f"Não foi possível obter credenciais de autenticação do firebase em '{firebase_credentials_path}', tentando localmente...")
        firebase_credentials_path = "config/firebase.json"
        if os.path.exists(firebase_credentials_path):
            message(f"Credenciais encontradas em '{firebase_credentials_path}'.")
        else:
            message(f"Não foi possível obter credenciais de autenticação do firebase em '{firebase_credentials_path}'.")
            return

    return firebase_credentials_path

def init_firestore(firebase_credentials_path):
    message("Conectando ao Firestore...")
    try:
        db = firestore.Client.from_service_account_json(firebase_credentials_path)
        message("Conexão ao Firestore estabelecida.")
    except Exception as e:
        message(f"Erro ao conectar no Firestore: {str(e)}")
        return

    return db


# -- uploads --
def upload_data(db, video_count, total_minutes):
    message(f"Salvando dados para {TODAY_STRING}: {video_count} vídeos, {total_minutes} minutos...")

    try:
        doc_ref = db.collection("playlist_data").document(TODAY_STRING)
        doc_ref.set({
            "video_count": video_count,
            "total_minutes": total_minutes
        }, merge=True)
        return message(f"Dados para {TODAY_STRING} salvos.", True)
    
    except Exception as e:
        message(f"Erro ao salvar dados: {str(e)}", True)
        return

def upload_status(db, title, status, success=False):
    message(f"Salvando status '{title}'...")

    try:
        last_title = title + "_timestamp"

        # timestamp = datetime.datetime.now(TIMEZONE).isoformat()
        timestamp = datetime.datetime.now(TIMEZONE)
        formatted_time = timestamp.strftime('%d/%m/%Y %H:%M:%S')

        doc_ref = db.collection("status").document("playlist_status")
        doc_ref.set({
            title: status,
            last_title: formatted_time,
            "success": success
        }, merge=True)
        message(f"Status salvo.")

    except Exception as e:
        message(f"Erro ao salvar status: {str(e)}")

def upload_calc(db, collection, document, title, data):
    message(f"Salvando '{title}' em '{collection}/{document}'...")

    try:
        doc_ref = db.collection(collection).document(document)
        doc_ref.set({
            title: data
        }, merge=True)
        message(f"Dados '{title}' salvos no Firestore.")

    except Exception as e:
        message(f"Erro salvar dados '{title}': {str(e)}")


# -- collect and save --
def check_data(db):
    message("Verificando se há dados existentes...")
    try:
        doc_ref = db.collection("playlist_data").document(TODAY_STRING)
        doc = doc_ref.get()
        if not doc.exists:  # Não há dados no dia atual
            return message("Dados ainda não inseridos no banco.")
        info_message = message(f"Dados para {TODAY_STRING} já salvos.", True)
        upload_status(db, "final_result", info_message, True)
        return
    
    except Exception as e:
        error_message = message(f"Erro ao verificar os dados: {str(e)}", True)
        upload_status(db, "final_result", error_message)
        return

def authenticate_youtube(db, youtube_api_key):
    message("Autenticando conta da API...")

    try:
        authentication = build("youtube", "v3", developerKey=youtube_api_key)
        message("Autenticação concluída.")
        return authentication
    except Exception as e:
        error_message = message(f"Erro na autenticação: {e}", True)
        upload_status(db, "final_result", error_message)
        return

def get_data(db, youtube_authentication, playlist_id):
    message(f"Obtendo dados da playlist '{playlist_id}'...")

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

        message(f"Playlist contém {video_count} vídeos e {total_minutes} minutos no total.")

    except Exception as e:
        error_message = message(f"Erro ao buscar os dados da playlist: {str(e)}", True)
        upload_status(db, "final_result", error_message)
        return None, None

    return video_count, total_minutes

def parse_duration_to_minutes(duration):
    # Regex para extrair os componentes de tempo do formato ISO 8601
    pattern = r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, duration)

    if not match:
        raise ValueError("Formato de duração inválido.")

    days = int(match.group(1)) if match.group(1) else 0
    hours = int(match.group(2)) if match.group(2) else 0
    minutes = int(match.group(3)) if match.group(3) else 0
    seconds = int(match.group(4)) if match.group(4) else 0

    # Converte para minutos
    total_minutes = days * 1440 + hours * 60 + minutes + seconds // 60
    return total_minutes


# -- parse and save data --
def fetch_data(db):
    message("Buscando dados no Firestore...")
    
    try:
        collection_ref = db.collection("playlist_data")
        docs = collection_ref.stream()
        
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            data.append({
                "date": doc.id,
                "video_count": doc_data.get("video_count", 0),
                "total_minutes": doc_data.get("total_minutes", 0)
            })

        if data:
            message(f"{len(data)} registros encontrados no Firestore.")
        else:
            message("Nenhum dado encontrado na coleção.")
    except Exception as e:
        error_message = message(f"Erro ao buscar os dados: {str(e)}", True)
        upload_status(db, "final_result", error_message)
        return

    message("Dados encontrados no Firestore.")
    return data

def parse_data(data):
    message("Separando dados...")

    video_points = [{"x": item["date"], "y": item["video_count"]} for item in data]
    minute_points = [{"x": item["date"], "y": item["total_minutes"]} for item in data]

    preprocessed_full_data = {
        "video_count_points": video_points,
        "total_minutes_points": minute_points
    }

    preprocessed_month_data = {
        "video_count_points": video_points[-28:],
        "total_minutes_points": minute_points[-28:]
    }

    message("Dados pré-processados.")
    return preprocessed_full_data, preprocessed_month_data


# -- calc and save data --
def calculate_changes(values, title):
    message(f"Calculando mudanças para {title}...")

    if not values:
        message(f"Nenhum valor para {title} encontrado.")
        return {}

    # mudanças dia a dia na última semana (até 7 dias)
    last_week_changes = [
        values[-i] - values[-i - 1]
        for i in range(1, min(7, len(values)))
    ]
    last_week_added   = sum(c for c in last_week_changes if c > 0)
    last_week_removed = sum(c for c in last_week_changes if c < 0)

    # mudanças dia a dia no último mês (até 28 dias)
    last_month_changes = [
        values[-i] - values[-i - 1]
        for i in range(1, min(28, len(values)))
    ]
    last_month_added   = sum(c for c in last_month_changes if c > 0)
    last_month_removed = sum(c for c in last_month_changes if c < 0)

    # mudanças dia a dia em todo o período
    total_changes = [
        values[i] - values[i - 1]
        for i in range(1, len(values))
    ]
    total_added   = sum(c for c in total_changes if c > 0)
    total_removed = sum(c for c in total_changes if c < 0)

    # diferenças pontuais
    last_day_difference    = values[-1] - values[-2] if len(values) > 1 else 0
    last_week_difference   = values[-1] - values[-7] if len(values) > 7 else 0
    last_month_difference  = values[-1] - values[-28] if len(values) > 28 else 0
    total_difference       = values[-1] - values[0]

    # médias
    last_week_average_change = (
        round(sum(last_week_changes) / len(last_week_changes), 2)
        if last_week_changes else 0
    )
    last_month_average_change = (
        round(sum(last_month_changes) / len(last_month_changes), 2)
        if last_month_changes else 0
    )
    total_average_change = (
        round(sum(total_changes) / len(total_changes), 2)
        if total_changes else 0
    )

    message(f"Cálculo para {title} finalizado.")
    return {
        # diferenças pontuais
        "last_day_difference": last_day_difference,
        "last_week_difference": last_week_difference,
        "last_month_difference": last_month_difference,
        "total_difference": total_difference,

        # apontamentos de adições e remoções
        "last_week_added": last_week_added,
        "last_week_removed": last_week_removed,
        "last_month_added": last_month_added,
        "last_month_removed": last_month_removed,
        "total_added": total_added,
        "total_removed": total_removed,

        # médias
        "last_week_average_change": last_week_average_change,
        "last_month_average_change": last_month_average_change,
        "total_average_change": total_average_change,
    }

def load_change_indicator(values, title):
    message(f"Calculando indicador de mudança para {title}...")
    if len(values) > 1:
        if values[-1] > values[-2]:
            return "↑"
        elif values[-1] < values[-2]:
            return "↓"
        else:
            return "●"
    return ""


# -- main functions --
def init():

    message("Iniciando paramêtros do script...")

    # Inicializa data do dia atual
    set_day()

    playlist_id, youtube_api_key, firebase_credentials_path = load_keys()

    # Definir ambiente
    firebase_credentials_path = set_environment(firebase_credentials_path)
    if not firebase_credentials_path: return message("Execução finalizada com falha.", True)

    # Faz a conexão com o firebase
    db = init_firestore(firebase_credentials_path)
    if not db: return message("Execução finalizada com falha.", True)

    message("Paramêtros inicializados.")
    return playlist_id, youtube_api_key, db

def collect_and_save(playlist_id, youtube_api_key, db):

    message("Iniciando coleta e salvamento de dados...")

    # Checa no firebase se já tem dados para hoje
    data_checked = check_data(db)
    if not data_checked: return

    # Autentica as credenciais do youtube
    youtube_authentication = authenticate_youtube(db, youtube_api_key)
    if not youtube_authentication: return

    # Coleta os dados de playlist
    video_count, total_minutes = get_data(db, youtube_authentication, playlist_id)
    if not video_count: return

    # Salva os dados no firebase
    data_uploaded = upload_data(db, video_count, total_minutes)
    if not data_uploaded: return

    # Salva o status de resultado final
    upload_status(db, "final_result", data_uploaded, True)
    return message("Fluxo de coletar e salvar dados finalizado.")

def parse_and_save_data(db):
    message("Iniciando salvamento de lista de pontos...")
    
    data = fetch_data(db)
    if not data: return

    full_data, month_data = parse_data(data)
    
    upload_calc(db, "parsed_data", "points_array", "month_data", month_data)
    # upload_calc(db, "parsed_data", "points_array", "full_data", full_data)
    
    message("Fluxo de salvar lista de pontos finalizado.")
    return full_data

def calc_and_save_data(db, data):
    message("Iniciando salvamento dos cálculos...")

    video_points = data["video_count_points"]
    minute_points = data["total_minutes_points"]

    video_counts = [pt["y"] for pt in video_points]
    total_minutes = [pt["y"] for pt in minute_points]

    video_changes = calculate_changes(video_counts, "vídeos")
    minute_changes = calculate_changes(total_minutes, "minutos")
    
    video_change_indicator = load_change_indicator(video_counts, "vídeos")
    minute_change_indicator = load_change_indicator(total_minutes, "minutos")
    video_changes["change_indicator"] = video_change_indicator
    minute_changes["change_indicator"] = minute_change_indicator

    current_videos = video_counts[-1]
    current_hours, current_minutes = divmod(total_minutes[-1], 60)
    video_changes["current_videos"] = current_videos
    video_changes["current_hours"] = current_hours
    video_changes["current_minutes"] = current_minutes

    minutes_per_video = round(total_minutes[-1] / video_counts[-1])
    minute_changes["minutes_per_video"] = minutes_per_video

    upload_calc(db, "parsed_data", "calcs", "video_changes", video_changes)
    upload_calc(db, "parsed_data", "calcs", "minute_changes", minute_changes)

    message("Fluxo de salvar cálculos finalizado.")

def main():
    
    message("Iniciando script...\n", True)

    playlist_id, youtube_api_key, db = init()

    response = collect_and_save(playlist_id, youtube_api_key, db)
    if not response: return
    
    data = parse_and_save_data(db)
    if not data: return

    calc_and_save_data(db, data)

    message("Script finalizado.\n", True)

if __name__ == "__main__":
    main()