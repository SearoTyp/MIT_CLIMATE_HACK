# Investment Tax Credit (ITC) rate
ITC_RATE = 0.06

# Define a function to calculate ITC based on the predicted total installation cost
def calculate_itc_from_prediction(wattage_mw, duration_hr, year):
    total_installation_cost = predict_total_installed_cost(wattage_mw, duration_hr, year)
    itc_value = total_installation_cost * ITC_RATE
    return itc_value

# Example usage
#wattage = 2  # in megawatts
#duration = 3  # in hours
#year = 2030  # prediction year

itc_amount = calculate_itc_from_prediction(wattage, duration, year)
print(f"ITC Amount for {wattage}MW {duration}Hr in {year}: ${itc_amount:,.2f}")
