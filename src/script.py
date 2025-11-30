# Import packages
import json
import pandas as pd

# Import input.txt data with your folder path  
file_path = 'input.txt' 
records = []
with open(file_path, 'r') as file:
    for line in file:
        line = line.strip()
        if line:
            records.append(json.loads(line))

# Convert to Pandas DataFrame
df = pd.DataFrame(records)

# Convert to datetime
df['time'] = pd.to_datetime(df['time'])

# Create columns for the day and week of the time value   
df['time'] = df['time'].dt.tz_localize(None) # Assumption: All of the transactions occured in the same time zone 
df['day'] = df['time'].dt.date
df['week'] = df['time'].dt.to_period('W').apply(lambda r: r.start_time) # Assumption: A week starts on a Monday and ends on a Sunday 

# Assumption: This program could be used with new data that may have other non-numerical values beside '$' and 'USD$'  
df['load_amount'] = pd.to_numeric(df['load_amount'].str.replace(r'[^\d.]', '', regex=True))

# Mondays Sanction: Doubles load_amount on a Monday
df.loc[df['time'].dt.dayofweek == 0, 'load_amount'] *= 2

# Sort by customer_id and time for cumulative calculations
df = df.sort_values(by=['customer_id', 'time']).reset_index(drop=True)

# Add cumulative daily and weekly load amount per customer and round by 2 to prevent float precision errors
df['daily_cumulative_load'] = df.groupby(['customer_id', 'day'])['load_amount'].cumsum().round(2)
df['weekly_cumulative_load'] = df.groupby(['customer_id', 'week'])['load_amount'].cumsum().round(2)

# Add order of daily transaction per customer
df['daily_transaction_order'] = df.groupby(['customer_id', 'day']).cumcount() + 1

# Create violation flags
df['daily_amount_violation'] = df['daily_cumulative_load'] > 5000
df['weekly_amount_violation'] = df['weekly_cumulative_load'] > 20000
df['daily_count_violation'] = df['daily_transaction_order'] > 3
df['accepted'] = (
    df['daily_amount_violation'] |
    df['weekly_amount_violation'] |
    df['daily_count_violation']
)

# Export output with your folder path
df[['id', 'customer_id', 'accepted']].to_json(
    'output.txt',
    orient='records',
    lines=True
)
