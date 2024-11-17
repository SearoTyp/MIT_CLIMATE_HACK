import pandas as pd
from sklearn.linear_model import LinearRegression

# Data for Fixed Operation and Maintenance Expenses ($/kW-yr)
data = {
    'Year': list(range(2022, 2051)),
    '1Hr': [
        34.92948094, 40.45098111, 37.84865946, 37.31179904, 35.91596195,
        34.52012487, 33.12428778, 31.72845069, 30.33261361, 30.2459958,
        30.159378, 30.0727602, 29.98614239, 29.89952459, 29.81290679,
        29.72628898, 29.63967118, 29.55305338, 29.46643557, 29.37981777,
        29.29319997, 29.20658216, 29.11996436, 29.03334656, 28.94672875,
        28.86011095, 28.77349315, 28.68687534, 28.60025754
    ],
    '2Hr': [
        41.80850349, 48.91926472, 45.30258591, 44.65999604, 42.98926238,
        41.31852871, 39.64779505, 37.97706138, 36.30632772, 36.20265138,
        36.09897504, 35.9952987, 35.89162236, 35.78794602, 35.68426968,
        35.58059334, 35.476917, 35.37324066, 35.26956432, 35.16588798,
        35.06221164, 34.9585353, 34.85485896, 34.75118262, 34.64750628,
        34.54382994, 34.4401536, 34.33647726, 34.23280092
    ],
    '4Hr': [
        55.5665486, 65.85583195, 60.21043883, 59.35639005, 57.13586323,
        54.9153364, 52.69480958, 50.47428276, 48.25375594, 48.11596253,
        47.97816911, 47.8403757, 47.70258229, 47.56478887, 47.42699546,
        47.28920205, 47.15140864, 47.01361522, 46.87582181, 46.7380284,
        46.60023499, 46.46244157, 46.32464816, 46.18685475, 46.04906134,
        45.91126792, 45.77347451, 45.6356811, 45.49788768
    ],
    '6Hr': [
        69.3245937, 82.79239917, 75.11829174, 74.05278405, 71.28246407,
        68.51214409, 65.74182412, 62.97150414, 60.20118416, 60.02927367,
        59.85736319, 59.6854527, 59.51354222, 59.34163173, 59.16972124,
        58.99781076, 58.82590027, 58.65398979, 58.4820793, 58.31016882,
        58.13825833, 57.96634785, 57.79443736, 57.62252687, 57.45061639,
        57.2787059, 57.10679542, 56.93488493, 56.76297445
    ],
    '8Hr': [
        83.08263881, 99.7289664, 90.02614465, 88.74917806, 85.42906492,
        82.10895179, 78.78883865, 75.46872551, 72.14861238, 71.94258482,
        71.73655726, 71.5305297, 71.32450214, 71.11847459, 70.91244703,
        70.70641947, 70.50039191, 70.29436435, 70.08833679, 69.88230924,
        69.67628168, 69.47025412, 69.26422656, 69.058199, 68.85217144,
        68.64614389, 68.44011633, 68.23408877, 68.02806121
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
    value_name='CostPerKWYr'
)

# Convert DurationHr to numeric (removing 'Hr')
melted_data['DurationHr'] = melted_data['DurationHr'].str.replace('Hr', '').astype(float)

# Merge the wattage data based on the duration (Hour column)
melted_data = melted_data.merge(wattage_data, left_on='DurationHr', right_on='Hour')

# Prepare the data for the regression model
X = melted_data[['Year', 'DurationHr']]  # Features: Year and Duration
y = melted_data['CostPerKWYr']  # Target: Cost per kW per year

# Train a linear regression model
model = LinearRegression()
model.fit(X, y)

# Define a function to retrieve exact cost if it exists
def get_exact_cost(year, duration_hr):
    """
    Retrieve the exact cost from the dataset for the given year and duration.
    """
    if str(duration_hr) + 'Hr' in cost_data.columns and year in cost_data['Year'].values:
        row = cost_data.loc[cost_data['Year'] == year]
        return row[str(duration_hr) + 'Hr'].values[0]
    return None

# Define a function to predict annual fixed operation and maintenance expenses
def predict_maintenance_cost(wattage_mw, duration_hr, year):
    """
    Predict the fixed operation and maintenance expenses annually based on
    wattage, duration, and year.
    """
    # Check for exact cost
    exact_cost_per_kw = get_exact_cost(year, duration_hr)
    if exact_cost_per_kw is not None:
        return exact_cost_per_kw * wattage_mw * 1000  # Convert MW to kW
    
    # Otherwise, use regression
    cost_per_kw_yr = model.predict([[year, duration_hr]])[0]
    return cost_per_kw_yr * wattage_mw * 1000

# Example usage
#wattage = 1.81  # in megawatts
#duration = 1  # in hours
#year = 2022  # prediction year
predicted_cost = predict_maintenance_cost(wattage, duration, year)
print(f"Predicted Annual Fixed O&M Cost for {wattage}MW {duration}Hr in {year}: ${predicted_cost:,.2f}")
