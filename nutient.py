import requests
from flask import Flask, jsonify, render_template_string, request, send_file
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


app = Flask('myapp')

# HTML Templates as Strings
index_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nutrient Finder</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f4f4f9;
            color: #333;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
            max-width: 400px;
            text-align: center;
        }

        h1 {
            font-size: 2rem;
            color: #27ae60;
            margin-bottom: 20px;
        }

        label {
            font-size: 1rem;
            color: #555;
            display: block;
            margin-bottom: 10px;
        }

        input[type="text"] {
            width: 100%;
            padding: 12px;
            margin-bottom: 20px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 1rem;
        }

        button {
            background-color: #27ae60;
            color: white;
            border: none;
            padding: 12px;
            font-size: 1rem;
            border-radius: 5px;
            cursor: pointer;
            width: 100%;
        }

        button:hover {
            background-color: #218c53;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Nutrient Finder</h1>
        <form method="POST">
            <label for="ingredient">Enter ingredient:</label>
            <input type="text" id="ingredient" name="ingredient" placeholder="e.g., Apple" required>
            <button type="submit">Get Nutrition Data</button>
        </form>
    </div>
</body>
</html>
'''

result_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nutrient Results</title>
     <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f5f5f5;
            color: #333;
            margin: 0;
            padding: 20px;
        }

        h1 {
            text-align: center;
            color: #4CAF50;
            margin-bottom: 30px;
        }

        .container {
            display: flex;
            justify-content: space-around;
            align-items: flex-start;
            margin-top: 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-right: 20px; /* Space between the table and pie chart */
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            background-color: #fff;
            border-radius: 8px; /* Rounded corners for the table */
            overflow: hidden; /* Ensures rounded corners are visible */
        }

        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            transition: background-color 0.3s;
        }

        th {
            background-color: #4CAF50;
            color: white;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        tr:hover {
            background-color: #f1f1f1;
        }

        img {
            max-width: 100%; /* Make the pie chart responsive */
            height: auto;
            border-radius: 8px; /* Rounded corners for the pie chart */
        }

        a {
            display: inline-block;
            margin: 20px auto;
            text-decoration: none;
            color: #4CAF50;
            font-weight: bold;
            text-align: center;
        }

        a:hover {
            text-decoration: underline;
        }
        .pie-chart-container {
    flex: 1;
    padding-left: 20px;
    display: flex;
    justify-content: center; /* Center the chart horizontally */
    align-items: center; /* Center the chart vertically */
    height: 100%; /* Ensures the container takes full height */
    # background-color: #fff; /* Background for contrast */
    border-radius: 8px; /* Rounded corners */
    # box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); /* Soft shadow */
    transition: transform 0.2s; /* Animation on hover */
}

.pie-chart-container:hover {
    transform: scale(1.01); /* Slight zoom on hover */
}

.pie-chart {
    max-width: 90%; /* Responsive width */
    height: auto; /* Maintain aspect ratio */
    border-radius: 8px; /* Rounded corners */
    border: 4px solid #4CAF50; /* Green border */
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* Inner shadow */
}

    </style>
</head>
<body>
    <h1>Nutrient Data for {{ ingredient }}</h1>
    <div style="display: flex;">
        <!-- Table with top 15 nutrients -->
        <div style="flex: 1;">
            <table border="1">
                <thead>
                    <tr>
                        <th>Nutrient</th>
                        <th>Quantity</th>
                        <th>Unit</th>
                    </tr>
                </thead>
                <tbody>
                    {% for nutrient, details in top_nutrients %}
                    <tr>
                        <td>{{ details['label'] }}</td>
                        <td>{{ details['quantity'] }}</td>
                        <td>{{ details['unit'] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <!-- Pie chart for top 6 nutrients -->
       <div class="pie-chart-container">
    <img src="{{ url_for('pie_chart') }}" alt="Nutrient Pie Chart" class="pie-chart">
</div>
    </div>
    <br>
    <a href="/">Go Back</a>
</body>
</html>
'''

# Global variables to store top 6 nutrient data and calories
top_6_nutrients = []
calories = 0

@app.route('/', methods=['GET', 'POST'])
def index():
    global top_6_nutrients, calories
    if request.method == 'POST':
        # Get the user input
        ingredient = request.form.get('ingredient')
        
        # Edamam API credentials (replace with your own app ID and app key)
        app_id = 'id'  # Replace with your actual app ID
        app_key = 'key'  # Replace with your actual app key
        
        # Edamam API URL
        url = 'https://api.edamam.com/api/nutrition-data'
        
        # Make the API request
        try:
            res = requests.get(url, params={'app_id': app_id, 'app_key': app_key, 'ingr': ingredient})
            
            if res.status_code != 200:
                return jsonify({"error": "Request failed", "status_code": res.status_code, "response": res.text}), res.status_code
            
            # Extract the nutrient and calorie data from the response
            data = res.json()
            nutrient_data = data.get('totalNutrients', {})
            calories = data.get('calories', 0)  # Store calories
            
            # Sort the nutrients by quantity in descending order and get the top 15
            sorted_nutrients = sorted(nutrient_data.items(), key=lambda x: x[1]['quantity'], reverse=True)
            top_nutrients = sorted_nutrients[:15]
            top_6_nutrients = sorted_nutrients[:6]  # Save top 6 for the pie chart
            
            # Render the result HTML with the top 15 sorted nutrient data
            return render_template_string(result_html, top_nutrients=top_nutrients, ingredient=ingredient)
        
        except Exception as e:
            return jsonify({"error": str(e), "response": res.text if 'res' in locals() else "No response"}), 500

    # Render the input form HTML
    return render_template_string(index_html)

@app.route('/pie-chart')
def pie_chart():
    global top_6_nutrients, calories
    
    # Prepare data for the pie chart
    labels = [x[1]['label'] for x in top_6_nutrients]
    sizes = [x[1]['quantity'] for x in top_6_nutrients]
    colors = plt.get_cmap('tab20').colors[:len(labels)]  # Get unique colors for each nutrient
    
    # Create pie chart
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
    # Add the calories text below the pie chart
    plt.figtext(0.5, 0.01, f"Total Calories: {calories}", ha="center", fontsize=12, color="blue")
    
    # Save the pie chart to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return send_file(img, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
