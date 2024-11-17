import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

# Data for yearly installed costs
data = {
    'Year': list(range(2022, 2051)),
    '1Hr': [
        2514922.627, 2912470.64, 2725103.481, 2686449.531, 2585949.261,
        2485448.99, 2384948.72, 2284448.45, 2183948.18, 2177711.698,
        2171475.216, 2165238.734, 2159002.252, 2152765.771, 2146529.289,
        2140292.807, 2134056.325, 2127819.843, 2121583.361, 2115346.88,
        2109110.398, 2102873.916, 2096637.434, 2090400.952, 2084164.47,
        2077927.988, 2071691.507, 2065455.025, 2059218.543
    ],
    '2Hr': [
        3010212.251, 3522187.06, 3261786.186, 3215519.715, 3095226.891,
        2974934.067, 2854641.243, 2734348.42, 2614055.596, 2606590.899,
        2599126.203, 2591661.506, 2584196.81, 2576732.113, 2569267.417,
        2561802.72, 2554338.024, 2546873.328, 2539408.631, 2531943.935,
        2524479.238, 2517014.542, 2509549.845, 2502085.149, 2494620.452,
        2487155.756, 2479691.059, 2472226.363, 2464761.666
    ],
    '4Hr': [
        4000791.499, 4741619.9, 4335151.595, 4273660.083, 4113782.152,
        3953904.221, 3794026.29, 3634148.359, 3474270.428, 3464349.302,
        3454428.176, 3444507.05, 3434585.925, 3424664.799, 3414743.673,
        3404822.548, 3394901.422, 3384980.296, 3375059.17, 3365138.045,
        3355216.919, 3345295.793, 3335374.668, 3325453.542, 3315532.416,
        3305611.29, 3295690.165, 3285769.039, 3275847.913
    ],
    '6Hr': [
        4991370.747, 5961052.74, 5408517.005, 5331800.452, 5132337.413,
        4932874.375, 4733411.336, 4533948.298, 4334485.259, 4322107.704,
        4309730.149, 4297352.595, 4284975.04, 4272597.485, 4260219.93,
        4247842.375, 4235464.82, 4223087.265, 4210709.71, 4198332.155,
        4185954.6, 4173577.045, 4161199.49, 4148821.935, 4136444.38,
        4124066.825, 4111689.27, 4099311.715, 4086934.16
    ],
    '8Hr': [
        5981949.994, 7180485.581, 6481882.415, 6389940.82, 6150892.674,
        5911844.529, 5672796.383, 5433748.237, 5194700.091, 5179866.107,
        5165032.123, 5150198.139, 5135364.154, 5120530.17, 5105696.186,
        5090862.202, 5076028.218, 5061194.233, 5046360.249, 5031526.265,
        5016692.281, 5001858.297, 4987024.312, 4972190.328, 4957356.344,
        4942522.36, 4927688.376, 4912854.391, 4898020.407
    ]
}

# Wattage data
wattage_data = {
    'Hour': [1, 2, 4, 6, 8],
    'Total Megawatt': [1.81, 3.62, 7.24, 10.86, 14.48]
}

# Convert both dictionaries to DataFrames
cost_data = pd.DataFrame(data)
wattage_data = pd.DataFrame(wattage_data)

# Reshape the cost data into a long format
melted_data = cost_data.melt(
    id_vars=['Year'], 
    var_name='DurationHr', 
    value_name='CostPerMW'
)

# Convert DurationHr to numeric (removing 'Hr')
melted_data['DurationHr'] = melted_data['DurationHr'].str.replace('Hr', '').astype(float)

# Merge the wattage data based on the duration (Hour column)
melted_data = melted_data.merge(wattage_data, left_on='DurationHr', right_on='Hour')

# Prepare the data for the regression model
X = melted_data[['Year', 'DurationHr', 'Total Megawatt']]  # Features: Year, Duration, Wattage
y = melted_data['TotalCostPerMW']

# Train a linear regression model
model = LinearRegression()
model.fit(X, y)

# Define a function to retrieve exact cost if it exists in the dataset
def get_exact_cost(duration_hr, year, wattage_mw):
    if str(duration_hr) + 'Hr' in cost_data.columns and year in cost_data['Year'].values:
        row = cost_data.loc[cost_data['Year'] == year]
        exact_cost = row[str(duration_hr) + 'Hr'].values[0]
        scale_factor = wattage_mw / wattage_data.loc[wattage_data['Hour'] == duration_hr, 'Total Megawatt'].values[0]
        return exact_cost * scale_factor
    return None

# Define a function to predict the cost
def predict_total_installed_cost(wattage_mw, duration_hr, year):
    exact_cost = get_exact_cost(duration_hr, year, wattage_mw)
    if exact_cost is not None:
        return exact_cost
    # Use regression model for values outside the dataset
    cost_per_mw = model.predict([[year, duration_hr, wattage_mw]])[0]
    total_cost = cost_per_mw 
    return total_cost

# Example usage
#wattage = 10  # in megawatts
#duration = 10  # in hours
#year = 2025  # prediction year
predicted_cost = predict_total_installed_cost(wattage, duration, year)
print(f"Predicted Installed Cost for {wattage}MW {duration}Hr in {year}: ${predicted_cost:,.2f}")
