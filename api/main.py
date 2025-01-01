from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow connections from any origin

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    try:
        # Load the file into a DataFrame
        df = pd.read_csv(file)

        # Example: Calculate statistics (for demonstration)
        stats = {
            "columns": list(df.columns),
            "rows": len(df),
            "summary": df.describe().to_dict()
        }

        # Mock anomaly detection output
        anomalies = df.sample(5).to_dict(orient='records')

        return jsonify({
            "stats": stats,
            "anomalies": anomalies
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
