import pandas as pd

df = pd.read_csv("C:/Users/rushi/OneDrive/Desktop/M.Tech/!st year 1st term/SM/Project/StudentsPerformance_1.csv")

# Pivot the data to create separate columns for each education level and score type
df_pivot = df.pivot_table(index=df.index, 
                          columns="parental level of education", 
                          values=["math score", "reading score", "writing score"], 
                          aggfunc="first")

# Flatten the MultiIndex columns
df_pivot.columns = [f"{score_type}_{edu_level.replace(' ', '_')}" for score_type, edu_level in df_pivot.columns]

# Convert the pivoted DataFrame to a dictionary
data_dict = df_pivot.to_dict(orient="list")

# Remove NaN values from the lists in the dictionary
for key in data_dict.keys():
    data_dict[key] = [x for x in data_dict[key] if not pd.isna(x)]

# Find the maximum length of the lists
max_len = max(len(lst) for lst in data_dict.values())

# Pad shorter lists with None (or NaN) to match the maximum length
for key in data_dict.keys():
    while len(data_dict[key]) < max_len:
        data_dict[key].append(None)  # You can replace `None` with `float('nan')` if needed

# Convert the cleaned data_dict back to a DataFrame
cleaned_df = pd.DataFrame(data_dict)

# Save the cleaned DataFrame to a CSV file
cleaned_df.to_csv("cleaned_data.csv", index=False)

# Optionally, print the DataFrame to verify
print(cleaned_df.head())
