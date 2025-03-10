from flask import Flask, request, render_template_string
import pandas as pd
from scipy.stats import f
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

rawhtml = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>One-Way ANOVA Calculator</title>
    <style>
        /* Dark Theme Styles */
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #121212; /* Dark background */
            color: #e0e0e0; /* Light text */
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        .container {
            margin-top: 50px;
            background-color: #1e1e1e; /* Slightly lighter dark background */
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
            width: 450px;
            text-align: center;
            animation: fadeIn 0.5s ease-in-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        h1 {
            margin-bottom: 20px;
            font-size: 24px;
            color: #64b5f6; /* Light blue for headings */
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #bdbdbd;
            text-align: left;
        }

        input[type="file"], input[type="text"] {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #424242; /* Darker border */
            border-radius: 6px;
            font-size: 14px;
            background-color: #303030; /* Darker input background */
            color: #e0e0e0;
            transition: border-color 0.3s ease;
        }

        input[type="file"]:focus, input[type="text"]:focus {
            border-color: #64b5f6;
            outline: none;
        }

        button {
            width: 100%;
            padding: 12px;
            background-color: #64b5f6;
            color: #121212;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        button:hover {
            background-color: #42a5f5;
        }

        #result {
            text-align: left;
            background-color: #212121; /* Slightly darker result background */
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            animation: slideIn 0.5s ease-in-out;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        #result h2 {
            margin-bottom: 15px;
            font-size: 20px;
            color: #64b5f6;
        }

        #result h3 {
            margin-bottom: 10px;
            font-size: 18px;
            color: #bdbdbd;
        }

        #result p {
            margin: 8px 0;
            font-size: 14px;
            color: #e0e0e0;
        }

        #result p strong {
            color: #bdbdbd;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>One-Way ANOVA Calculator</h1>
        {% if not result %}
            <form method="POST" enctype="multipart/form-data">
                <label for="csvFile">Upload CSV File:</label>
                <input type="file" id="csvFile" name="csvFile" accept=".csv" required>
                
                <label for="groupColumn">Group Column:</label>
                <input type="text" id="groupColumn" name="groupColumn" placeholder="Enter group column name" required>
                
                <label for="variableColumn">Variable Column:</label>
                <input type="text" id="variableColumn" name="variableColumn" placeholder="Enter variable column name" required>
                
                <button type="submit">Calculate ANOVA</button>
            </form>
        {% endif %}

        {% if result %}
            <div id="result">
                <h2>One-Way ANOVA Results</h2>
                <h3>Hypotheses</h3>
                <p><strong>Null Hypothesis (H₀):</strong> All group means are equal (μ₁ = μ₂ = ... = μₖ).</p>
                <p><strong>Alternative Hypothesis (H₁):</strong> At least one group mean is different.</p>

                <h3>Results</h3>
                <p><strong>Sum of Squares Between (SSB):</strong> {{ result.ssb | round(4) }}</p>
                <p><strong>Sum of Squares Within (SSW):</strong> {{ result.ssw | round(4) }}</p>
                <p><strong>Sum of Squares Total (SST):</strong> {{ result.sst | round(4) }}</p>
                <p><strong>Degrees of Freedom Between:</strong> {{ result.df_between }}</p>
                <p><strong>Degrees of Freedom Within:</strong> {{ result.df_within }}</p>
                <p><strong>Mean Square Between (MSB):</strong> {{ result.msb | round(4) }}</p>
                <p><strong>Mean Square Within (MSW):</strong> {{ result.msw | round(4) }}</p>
                <p><strong>F-Statistic:</strong> {{ result.f_statistic | round(4) }}</p>
                <p><strong>P-Value:</strong> {{ result.p_value | round(10) }}</p>
                <p><strong>F-Critical (α=0.05):</strong> {{ result.f_critical | round(4) }}</p>
                <p><strong>Group Column:</strong> {{ result.group_column }}</p>
                <p><strong>Variable Column:</strong> {{ result.variable_column }}</p>
                <p><strong>Groups:</strong> {{ result.groups | join(', ') }}</p>

                <h3>Conclusion</h3>
                {% if result.p_value < 0.05 %}
                    <p><strong>Conclusion:</strong> Reject the null hypothesis (H₀). There is a statistically significant difference between at least two group means.</p>
                {% else %}
                    <p><strong>Conclusion:</strong> Fail to reject the null hypothesis (H₀). There is no statistically significant difference between the group means.</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>"""

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the uploaded file
        file = request.files['csvFile']
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            # Get the group and variable columns
            group_column = request.form['groupColumn']
            variable_column = request.form['variableColumn']

            # Read the CSV file
            df = pd.read_csv(filepath)

            # Check if columns exist in the CSV
            if group_column not in df.columns or variable_column not in df.columns:
                return "Error: The specified columns do not exist in the CSV file."

            # Perform one-way ANOVA calculations
            result = calculate_anova(df, group_column, variable_column)

            # Delete the file after processing
            os.remove(filepath)

            return render_template_string(rawhtml, result=result)

        else:
            return "Error: Please upload a valid CSV file."

    return render_template_string(rawhtml, result=None)

def calculate_anova(df, group_column, variable_column):
    # Extract groups
    groups = df.groupby(group_column)[variable_column].apply(list)
    group_means = groups.apply(lambda x: sum(x) / len(x))
    overall_mean = df[variable_column].mean()

    # Calculate SSB (Sum of Squares Between)
    ssb = sum(len(group) * (group_mean - overall_mean) ** 2 for group, group_mean in zip(groups, group_means))

    # Calculate SSW (Sum of Squares Within)
    ssw = sum(sum((x - group_mean) ** 2 for x in group) for group, group_mean in zip(groups, group_means))

    # Calculate SST (Sum of Squares Total)
    sst = ssb + ssw

    # Degrees of freedom
    df_between = len(groups) - 1  # df between groups
    df_within = len(df) - len(groups)  # df within groups

    # Mean Squares
    msb = ssb / df_between  # Mean Square Between
    msw = ssw / df_within  # Mean Square Within

    # F-statistic
    f_statistic = msb / msw

    # p-value
    p_value = f.sf(f_statistic, df_between, df_within)

    # F-critical (using alpha = 0.05)
    alpha = 0.05
    f_critical = f.ppf(1 - alpha, df_between, df_within)

    # Prepare the result
    result = {
        'ssb': ssb,
        'ssw': ssw,
        'sst': sst,
        'df_between': df_between,
        'df_within': df_within,
        'msb': msb,
        'msw': msw,
        'f_statistic': f_statistic,
        'p_value': p_value,
        'f_critical': f_critical,
        'group_column': group_column,
        'variable_column': variable_column,
        'groups': groups.index.tolist(),
    }

    return result

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8001)
