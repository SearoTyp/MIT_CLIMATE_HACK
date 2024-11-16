import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

class Battery():
    def __init__(self, capacity):
        self.capacity = capacity # Total battery capacity (MWh)
        self.stored = 0 # Energy currently stored (MWh)

    def charge(self, rate):
        # Charge and discharge in 1 hour intervals
        # rate given in MW
        if self.stored + rate >= self.capacity:
            self.stored = self.capacity
        else:
            self.stored = self.stored + rate
    
    def discharge(self, rate):
        if self.stored - rate < 0:
            self.stored = 0
            return self.stored
        else:
            self.stored = self.stored - rate
            return rate

power_data = pd.read_csv('data/miso/miso_merged.csv') # TODO: abstract
power_data['datetime'] = pd.to_datetime(power_data['Local Timestamp Eastern Standard Time (Interval Ending)']) 

class Sim():
    def __init__(self, site, battery_capacity, discharge_price):
        site_data = pd.read_csv(f'data/{site.lower()}.csv')
        site_data['datetime'] = pd.to_datetime(site_data['Timestamp'])
        self.data = pd.merge(power_data, site_data, on='datetime')

        self.site = site
        self.discharge_price = discharge_price
        self.battery = Battery(battery_capacity)
    
        self.battery_revenue = []
        self.battery_stored = []

    def update(self, dt):
        if isinstance(dt, str):
            row = self.data[self.data['datetime'] == pd.to_datetime(dt)].iloc[0]
        else:
            row = self.data[self.data['datetime'] == dt].iloc[0]

        # If curtailment is > 0, charge the battery
        if row['Curtailment (MWh)'] > 0:
            self.battery.charge(row['Curtailment (MWh)'])
            self.battery_revenue.append([dt, 0])
            self.battery_stored.append([dt, self.battery.stored])
            return
        
        # Else, check if battery should be discharged
        if row['MISO Total Forecast Load (MW)'] <= row['MISO Total Total Generation (MW)']: # TODO: abstract
            # Power supply is exceeding demand; can't add more supply from battery
            self.battery_revenue.append([dt, 0])
            self.battery_stored.append([dt, self.battery.stored])
            return

        # Demand is exceeding supply, we can supply from battery
        # Check price theshold
        if row['Price ($/MWh) at the nodal level in the Real Time market'] < self.discharge_price:
            # Current price too low
            self.battery_revenue.append([dt, 0])
            self.battery_stored.append([dt, self.battery.stored])
            return
        
        # Discharge battery
        # TODO: calculate discharge rate from diff of actual price vs threshold
        discharge_rate = 1
        supplied = self.battery.discharge(discharge_rate)
        revenue = supplied * row['Price ($/MWh) at the nodal level in the Real Time market']
        self.battery_revenue.append([dt, revenue])
        self.battery_stored.append([dt, self.battery.stored])
        return
    
    def run(self):
        dts = self.data['datetime'].values

        t0 = time.time()
        print('Running simulation...')
        for dt in dts:
            self.update(dt)
        t1 = time.time()
        print(f'Simulation ran in {t1-t0:.2f} seconds')

    def plot(self):
        revenue = pd.DataFrame(self.battery_revenue, columns=['datetime', 'revenue'])
        stored = pd.DataFrame(self.battery_stored, columns=['datetime', 'battery capacity'])

        #fig, axs = plt.subplots(2, 1, figsize=(12,12), sharex=True)

        #axs[0].plot(revenue['datetime'], revenue['revenue'])
        #axs[0].set_xlabel('Date-time')
        #axs[0].set_ylabel('Revenue Earned from Battery Power ($)')

        #axs[1].plot(stored['datetime'], stored['battery capacity'])
        #axs[1].set_xlabel('Date-time')
        #axs[1].set_ylabel('Stored Battery Capacity (MW)')


        fig = plt.figure(figsize=(12,6))

        revenue['day'] = revenue['datetime'].dt.day_of_year
        revenue['month'] = revenue['datetime'].dt.month

        monthly = revenue.groupby('month')['revenue'].sum()

        plt.bar(monthly.index, monthly.values)
        plt.xlabel('Month')
        plt.ylabel('Revenue Gained ($)')
        plt.title(f'Monthly Revenue Gained from Battery Output ({self.battery.capacity} MW Capacity)')
        plt.text(1, 8000, f'Total Yearly Revenue: ${revenue["revenue"].sum()}')

        plt.savefig('plt')


if __name__ == "__main__":
    sim = Sim('Mantero', 10, 20)
    sim.run()
    revenue = pd.DataFrame(sim.battery_revenue, columns=['datetime', 'revenue'])
    stored = pd.DataFrame(sim.battery_stored, columns=['datetime', 'battery capacity'])
    
    total_rev =revenue['revenue'].sum()
    print(f'Total revenue gained: {total_rev:.2f}')

    sim.plot()