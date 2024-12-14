from flask import Flask, request, jsonify, render_template
from elasticsearch import Elasticsearch
from pymongo import MongoClient
from redis import Redis
from dotenv import load_dotenv
import os
import json
import csv
import io

load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

es = Elasticsearch(os.getenv("ELASTICSEARCH_HOST"))

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
mongo_db = mongo_client[os.getenv("MONGO_DB_NAME", "logs_db")]
mongo_collection = mongo_db[os.getenv("MONGO_COLLECTION_NAME", "logs")]

redis_client = Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6380))
)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_logs():
    file = request.files['file']
    filename = file.filename.lower()

    if filename.endswith('.csv'):
        stream = io.StringIO(file.read().decode('utf-8'))
        csv_reader = csv.DictReader(stream)
        logs = list(csv_reader)
    elif filename.endswith('.json'):
        logs = json.load(file)
    else:
        return "Unsupported file format. Only CSV and JSON are allowed.", 400

    for log in logs:
        es.index(index='logs', document=log)
        mongo_collection.insert_one(log)

    return "Logs uploaded successfully", 200

@app.route('/search', methods=['GET'])
def search_logs():
    query = request.args.get('query')

    response = es.search(index="logs", query={"match": {"message": query}})
    return jsonify(response['hits'])

@app.route('/kibana_dashboard')
def kibana_dashboard():
    dashboard_id = request.args.get('dashboard_id', 'default')
    kibana_url = f"{os.getenv('KIBANA_API', 'http://localhost:5601')}/app/kibana#/dashboard/{dashboard_id}"
    return render_template('kibana_dashboard.html', kibana_url=kibana_url)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
