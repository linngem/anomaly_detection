from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
from sklearn.ensemble import IsolationForest
from flask_cors import CORS



app = Flask(__name__,  static_folder='static')
CORS(app)
@app.route('/')
def index():

    #backend_url = 'http://127.0.0.1:5000'  # Set backend URL dynamically for production
    return render_template('index.html')


@app.route('/get_columns', methods=['POST'])
def get_columns():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Invalid file format. Please upload a CSV file."}), 400

    try:
        # Read the CSV file
        df = pd.read_csv(file)

        # Normalize column names: strip whitespace and convert to lowercase
        df.columns = df.columns.str.strip().str.lower()

        # Return the column names
        return jsonify({"columns": list(df.columns)})

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Invalid file format. Please upload a CSV file."}), 400
    
    try:
        # Load the file into a DataFrame
        df = pd.read_csv(file)

        # Get the columns from the form data
        columns = request.form.get('columns')
        contamination = request.form.get('contamination', 0.05)  # Default contamination is 0.05 if not provided
        contamination = float(contamination)  # Ensure it's a float
        
        if columns:
            columns = json.loads(columns)  # Parse the JSON string into a Python list

        # Normalize column names: strip whitespace and convert to lowercase
        df.columns = df.columns.str.strip().str.lower()

        # Check if the requested columns exist in the DataFrame
        invalid_columns = [col for col in columns if col not in df.columns]
        if invalid_columns:
            return jsonify({"error": f"Invalid columns: {', '.join(invalid_columns)}"}), 400

        # Select the requested columns
        selected_data = df[columns]

        # Ensure data is numeric and non-empty
        selected_data = selected_data.apply(pd.to_numeric, errors='coerce')  # Convert to numeric, replacing invalid values with NaN
        selected_data = selected_data.dropna()  # Drop rows with NaN values

        if selected_data.empty:
            return jsonify({"error": "The selected columns contain no valid numeric data."}), 400

        # Log the data to verify it's valid
        print("Data passed to IsolationForest:")
        print(selected_data)

        # Perform anomaly detection on the selected columns
        isolation_forest = IsolationForest(contamination=contamination)
        anomalies = isolation_forest.fit_predict(selected_data)

        # Add the anomaly labels to the DataFrame
        df['anomaly'] = anomalies

        # Stats summary
        stats = {
            "columns": list(df.columns),
            "rows": len(df),
            "summary": df.describe().to_dict(),
        }

        # Convert anomalies to a list of dictionaries
        anomalies_list = anomalies.tolist()  # Convert ndarray to list

        # Count the number of anomalies and calculate percentage
        anomaly_count = (df['anomaly'] == -1).sum()  # Count anomalies where the label is -1
        anomaly_percentage = (anomaly_count / len(df)) * 100  # Calculate the percentage of anomalies

        return jsonify({
            "stats": stats,
            "anomalies": anomalies_list,
            "anomaly_percentage": anomaly_percentage,
            "debug": {
                "selected_data": selected_data.to_dict(orient='records'),
                "anomaly_predictions": anomalies_list,
                "anomaly_percentage": anomaly_percentage
            }
        })

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
