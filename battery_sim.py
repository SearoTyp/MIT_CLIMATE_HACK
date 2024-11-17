import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

class Battery():
    def __init__(self, wattage_mw, duration_h, cycle_life, cycle_age):
        self.max_rate = wattage_mw # Max charge/discharge rate (MW)
        self.duration = duration_h # Battery duration (hours)

        # Assuming degredation is linear up to rated cycle life
        max_capacity = wattage_mw * duration_h # MWh
        self.capacity = max_capacity * (1 - (cycle_age / cycle_life)*0.2) # Cycle life defined to 80% original capacity

        self.stored = 0 # Energy currently stored (MWh)
        self.charge_total = 0 # Total MWh charged
        self.discharge_total = 0 # Total MWh discharged

        self.cycles = 0

        self.charging = False
        self.cycles_basic = 0

    def charge(self, rate):
        # Always 1 hour intervals
        overflow = 0
        if rate > self.max_rate: # If available MWh exceeds how much can be charged in 1 hr, we lose that power
            overflow = rate - self.max_rate
            rate = self.max_rate

        if self.stored + rate >= self.capacity:
            self.charge_total += self.capacity - self.stored
            overflow += self.capacity - self.stored # any excess power that can't fit in battery is overflow
            self.stored = self.capacity
        else:
            self.charge_total += rate
            self.stored = self.stored + rate
        
        self.charging = True            

        return overflow
    
    def discharge(self, rate):
        if rate > self.max_rate:
            rate = self.max_rate

        if self.charging:
            self.cycles_basic += 1
            self.charging = False

        if self.stored - rate < 0:
            self.discharge_total += self.stored
            self.stored = 0
            return self.stored
        else:
            self.discharge_total += rate
            self.stored = self.stored - rate
            return rate

class YearSim():
    def __init__(self, site, battery_wattage, battery_duration, charge_price, discharge_price, cycle_life, cycle_age):
        self.data = pd.read_csv(f'data/{site.lower()}.csv')
        self.data['datetime'] = pd.to_datetime(self.data['Timestamp'])

        self.site = site
        self.charge_price = charge_price
        self.discharge_price = discharge_price
        self.battery = Battery(battery_wattage, battery_duration, cycle_life, cycle_age)
    
        self.battery_revenue = []
        self.direct_revenue = []
        self.power_lost = []

    def update(self, dt):
        if isinstance(dt, str):
            row = self.data[self.data['datetime'] == pd.to_datetime(dt)].iloc[0]
        else:
            row = self.data[self.data['datetime'] == dt].iloc[0]

        current_price = row['Price ($/MWh) at the nodal level in the Real Time market']
        delivered = row['Energy actually delivered (MWh)']

        # If curtailment is > 0, charge the battery
        if row['Curtailment (MWh)'] > 0:
            overflow = self.battery.charge(row['Curtailment (MWh)'])
            self.battery_revenue.append([dt, 0])
            self.direct_revenue.append([dt, delivered*current_price])
            self.power_lost.append([dt, overflow])
            return
        
        # if current price is below set threshold, charge battery 
        elif current_price <= self.charge_price:
            overflow = self.battery.charge(delivered)
            self.battery_revenue.append([dt,0])

            if current_price <= 0: # don't send remaining energy to grid
                self.direct_revenue.append([dt, 0])
                self.power_lost.append([dt, overflow])
            else: # send remaining power
                self.direct_revenue.append([dt, overflow*current_price])
                self.power_lost.append([dt,0])
            
            return

        # if price is above threshold, discharge battery
        if current_price >= self.discharge_price:
            # TODO: modulate discharge rate from current price
            discharge_rate = self.battery.max_rate
            supplied = self.battery.discharge(discharge_rate)
            self.battery_revenue.append([dt, supplied*current_price])
            self.direct_revenue.append([dt, delivered*current_price])
            self.power_lost.append([dt,0])
            return
        
        # No charge or discharge
        self.battery_revenue.append([dt, 0])
        self.direct_revenue.append([dt, delivered*current_price])
        self.power_lost.append([dt, 0])
    
    def run(self, print_output=False):
        dts = self.data['datetime'].values

        if print_output:
            t0 = time.time()
            print('Running simulation...')
        
        for dt in dts:
            self.update(dt)
        
        if print_output:
            t1 = time.time()
            print(f'Simulation ran in {t1-t0:.2f} seconds')

        charge_cycles = self.battery.charge_total // self.battery.capacity
        discharge_cycles = self.battery.discharge_total // self.battery.capacity
        self.battery.cycles = min([charge_cycles, discharge_cycles])

    def plot_revenue(self, filename='fig_rev'):
        revenue = pd.DataFrame(self.battery_revenue, columns=['datetime', 'revenue'])

        fig = plt.figure(figsize=(12,6))

        revenue['day'] = revenue['datetime'].dt.day_of_year
        revenue['month'] = revenue['datetime'].dt.month

        monthly = revenue.groupby('month')['revenue'].sum()

        plt.bar(monthly.index, monthly.values)
        plt.xlabel('Month')
        plt.ylabel('Revenue Gained ($)')
        plt.title(f'Monthly Revenue Gained from Battery Output ({self.battery.capacity} MWh Capacity)')
        plt.text(1, monthly.max()*0.95, f'Total Yearly Revenue: ${revenue["revenue"].sum():.2f}')

        plt.savefig(filename)
    
    def plot_thresholds(self, filename='fig_thresh'):
        charging = self.data[(self.data['Price ($/MWh) at the nodal level in the Real Time market'] <= self.charge_price) | (self.data['Curtailment (MWh)'] > 0)]
        discharging = self.data[(self.data['Price ($/MWh) at the nodal level in the Real Time market'] >= self.discharge_price)]

        fig = plt.figure(figsize=(12,6))

        plt.plot(self.data['datetime'], self.data['Price ($/MWh) at the nodal level in the Real Time market'], c='black')
        plt.plot(charging['datetime'], charging['Price ($/MWh) at the nodal level in the Real Time market'], label='Charging')
        plt.plot(discharging['datetime'], discharging['Price ($/MWh) at the nodal level in the Real Time market'], label='Discharging')
        
        plt.legend()
        plt.xlabel('date/time')
        plt.ylabel('Price ($/MWh)')

        plt.savefig(filename)


CYCLE_LIFE = {}
CYCLE_LIFE['lithium-ion'] = 2000

def revenue_calc(site, battery_type, battery_power_MW, battery_duration_H, discharge_price, charge_price=0, cycle_life=None):
    if cycle_life is None:
        cycle_life = CYCLE_LIFE[battery_type]
    
    revenues = {}

    first_year = YearSim(site, battery_wattage=battery_power_MW, battery_duration=battery_duration_H, charge_price=charge_price, discharge_price=discharge_price, cycle_life=cycle_life, cycle_age=0)
    first_year.run()
    fy_revenue = pd.DataFrame(first_year.battery_revenue, columns=['datetime', 'revenue'])
    revenues['year_0'] = fy_revenue['revenue'].sum()

    cycles = first_year.battery.cycles
    lifespan = int(cycle_life // cycles)
    print(lifespan)

    for y in range(1, lifespan):
        sim = YearSim(site, battery_wattage=battery_power_MW, battery_duration=battery_duration_H, charge_price=charge_price, discharge_price=discharge_price, cycle_life=cycle_life, cycle_age=cycles)
        sim.run()
        revenue = pd.DataFrame(sim.battery_revenue, columns=['datetime', 'revenue'])
        revenues[f'year_{y}'] = revenue['revenue'].sum()
        cycles += sim.battery.cycles
        print(f'${revenue["revenue"].sum():.2f}')
    
    return revenues

if __name__ == "__main__":
    revenues = revenue_calc('Mantero', 'lithium-ion', 10, 5, 50, 15)

    import json
    with open('test_results.json', 'w') as f:
        json.dump(revenues, f, indent=2)
    """
    sim = YearSim('Mantero', battery_wattage=10, battery_duration=5, charge_price=0, discharge_price=50, cycle_life=2000, cycle_age=0)
    sim.run(True)
    revenue = pd.DataFrame(sim.battery_revenue, columns=['datetime', 'revenue'])
    
    revenue['month'] = revenue['datetime'].dt.month
    monthly = revenue.groupby('month')['revenue'].sum()
    for i in range(len(monthly)):
        print(f'{i+1}: {monthly.iloc[i]}')

    total_rev = revenue['revenue'].sum()
    print(f'Total revenue gained: {total_rev:.2f}')

    cycles = sim.battery.cycles
    print(f'{cycles} full charge cycles completed')
    print(f'{sim.battery.cycles_basic} charge cycles')
    print(f'Lifespan: {2000/sim.battery.cycles_basic}')

    sim.plot_revenue()
    sim.plot_thresholds()
    """