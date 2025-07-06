import pandas as pd

# Load the data
time_matrix_path = "time_matrix.csv"
time_matrix = pd.read_csv(time_matrix_path)

# Generate sorted list of locations
locations = sorted(time_matrix['FROM'].unique(), key=lambda x: int(x.replace('LOC', '')))

# Create adjacency matrix
time_matrix = time_matrix.pivot(index='FROM', columns='TO', values='XFER_TIME')
time_matrix = time_matrix.reindex(index=locations, columns=locations)

# Input indices as integers referring to LOC numbers
i, j = map(int, input().split())

# Convert to label strings
from_label = f"LOC{i}"
to_label = f"LOC{j}"

# Retrieve and print the value
print(time_matrix.loc[from_label, to_label])
