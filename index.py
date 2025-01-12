from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
from sklearn.ensemble import IsolationForest
from flask_cors import CORS
import plotly.express as px
import base64

app = Flask(__name__, static_folder='static')
CORS(app)

@app.route('/')
def index():
    result = {"anomalies": []}
    return render_template('index.html', result=result)

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

        # Pass anomalies in the response so they can be used in the plotting route
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

@app.route('/plot', methods=['POST', 'OPTIONS'])
def plot():
    try:
        # Get the X-axis column and anomalies from the request
        x_axis = request.form.get('x_axis')
        anomalies = request.form.get('anomalies')

        if not x_axis or not anomalies:
            return jsonify({"error": "Missing required data (x_axis or anomalies)."}), 400

        # Convert anomalies back to a list of integers
        anomalies = json.loads(anomalies)

        # Retrieve the uploaded file to get the DataFrame
        file = request.files.get('file')
        if not file:
            return jsonify({"error": "No file provided"}), 400

        # Load the file into a DataFrame
        df = pd.read_csv(file)

        # Normalize column names: strip whitespace and convert to lowercase
        df.columns = df.columns.str.strip().str.lower()

        # Ensure the column exists in the DataFrame
        if x_axis not in df.columns:
            return jsonify({"error": f"Column '{x_axis}' does not exist in the uploaded data."}), 400
        
        # Map anomaly values to 1 for 'Normal' and 0 for 'Anomaly'
        df['anomaly'] = [1 if x == -1 else 0 for x in anomalies]

        

        # Create a histogram plot using Plotly
        fig = px.histogram(df, x=x_axis, color='anomaly', barmode='overlay',
                   labels={'anomaly': 'Anomaly Status'}, category_orders={'anomaly': [0, 1]})
        fig.update_layout(title=f"Metric Distribution for Anomalies vs. Non-Anomalies for {x_axis}", xaxis_title="", yaxis_title="")
        fig.update_layout(width=1000, height=300)
        fig.show()

                # Convert to PNG and encode to base64
        img_bytes = fig.to_image(format='png')
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        # Return the image as base64 in the response
        response = jsonify({'image': f'data:image/png;base64,{img_base64}'})

        # Before returning the response
        print(response.get_data(as_text=True))  # This will print the response content

       
        # Return the image as base64 in the response    
        return jsonify({'image': f'data:image/png;base64,{img_base64}'})
        

    except Exception as e:
        return jsonify({"error": f"An error occurred while generating the plot: {str(e)}"}), 500

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
