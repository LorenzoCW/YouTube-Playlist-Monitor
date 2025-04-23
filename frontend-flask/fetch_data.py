from flask import Flask, render_template
from dotenv import load_dotenv
from google.cloud import firestore
import plotly.graph_objects as go
import os
import time
import logging
import pytz

# Configurações
debug = False
debug_time = 2

TIMEZONE = pytz.timezone("America/Sao_Paulo")
TODAY_STRING = ""

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(message)s',
        handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

app = Flask(__name__, template_folder="templates", static_folder="static")

def message(text, forced=False):
    if debug or forced:
        logger.info(text)
    if debug:
        time.sleep(debug_time)
    return text


# -- init --
def load_keys():
    message("Carregando variáveis secretas...")
    
    load_dotenv()
    firebase_credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')

    return firebase_credentials_path

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


# -- load data --
def fetch_status(db):
    message("Buscando status no Firestore...")

    doc_ref = db.collection("status").document("playlist_status")
    doc = doc_ref.get().to_dict() or {}

    status = {
        "final_result": doc.get("final_result", ""),
        "final_result_timestamp": doc.get("final_result_timestamp", ""),
        "success": doc.get("success", ""),
    }

    message("Status encontrados no Firestore.")
    return status

def fetch_points(db):
    message("Buscando dados de pontos do mês...")
    try:
        doc_ref = db.collection("parsed_data").document("points_array")
        doc = doc_ref.get()
        points = doc.to_dict().get("month_data", {})
        video_points = points.get("video_count_points", [])
        minute_points = points.get("total_minutes_points", [])
        message(f"Obtidos {len(video_points)} pontos de vídeo e {len(minute_points)} pontos de minutos.")
        return video_points, minute_points

    except Exception as e:
        message(f"Erro ao buscar dados do mês: {e}")
        return [], []

def generate_graph(dates, metric, title, color):
    message(f"Gerando gráfico de {title}...")
    try:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=metric,
                mode="lines+markers",
                line=dict(color=color),
                name=f"{title}: {metric[-1] if metric else 0}"
            )
        )

        fig.update_layout(
            xaxis_title="Data",
            yaxis_title=title,
            yaxis=dict(side="right"),
            template="plotly_dark",
            height=375,
        )

        graph_html = fig.to_html(full_html=False)
        message(f"Gráfico de {title} gerado.")
        return graph_html

    except Exception as e:
        message(f"Erro ao gerar gráfico de {title}: {e}")
        return f"<p>Nenhum dado de {title} para mostrar.</p>"

def fetch_calculations(db):
    message("Buscando informações...")
    try:
        doc_ref = db.collection("parsed_data").document("calcs")
        doc = doc_ref.get()
        data = doc.to_dict() or {}
        video_changes = data.get("video_changes", {})
        minute_changes = data.get("minute_changes", {})
        message("Informações coletadas.")
        return video_changes, minute_changes
    
    except Exception as e:
        message(f"Erro ao buscar informações: {e}")
        return {}, {}


# -- main functions --
def init():

    message("Iniciando paramêtros do script...")

    firebase_credentials_path = load_keys()

    # Definir ambiente
    firebase_credentials_path = set_environment(firebase_credentials_path)
    if not firebase_credentials_path: return message("Execução finalizada com falha.", True)

    # Faz a conexão com o firebase
    db = init_firestore(firebase_credentials_path)
    if not db: return message("Execução finalizada com falha.", True)

    message("Paramêtros inicializados.")
    return db

def load_data(db):
    message("Buscando status e dados...")

    status = fetch_status(db)

    video_points, minute_points = fetch_points(db)

    dates = [pt['x'] for pt in video_points]
    video_counts = [pt['y'] for pt in video_points]
    total_minutes = [pt['y'] for pt in minute_points]

    video_graph = generate_graph(dates, video_counts, "Vídeos", "firebrick")
    minute_graph = generate_graph(dates, total_minutes, "Minutos", "dodgerblue")

    video_changes, minute_changes = fetch_calculations(db)

    message("Status e dados carregados.")
    return status, video_graph, minute_graph, video_changes, minute_changes


# -- rotas --
@app.route("/")
def show_graph():
    message("Carregando dados...")

    db = init()
    status, video_graph, minute_graph, video_changes, minute_changes = load_data(db)

    message("Dados carregados.")
    return render_template(
        "graph.html",
        status = status,
        video_graph = video_graph,
        minute_graph = minute_graph,
        video_changes = video_changes,
        minute_changes = minute_changes,
    )

if __name__ == "__main__":
    app.run()