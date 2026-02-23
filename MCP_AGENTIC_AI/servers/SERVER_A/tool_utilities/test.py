

import os
from pathlib import Path




def execute_plotting_agent(user_query, shared_folder,csv_filename):

    shared_folder = Path(shared_folder)
    shared_folder_parent = shared_folder.parent

    csv_path = shared_folder / csv_filename


            # Direct path check
    if not csv_path.is_file():

        print("CSV not found in shared folder. Searching recursively...")

        # Search recursively starting from shared folder parent
        search_root = shared_folder_parent

        all_csvs = list(search_root.rglob("*.csv"))

        print(f"Total CSVs found recursively: {len(all_csvs)}")

        if all_csvs:
            # Prefer files inside the shared folder first
            preferred = [f for f in all_csvs if shared_folder in f.parents]

            if preferred:
                csv_path = max(preferred, key=lambda x: x.stat().st_mtime)
            else:
                csv_path = max(all_csvs, key=lambda x: x.stat().st_mtime)

            print(f"CSV selected: {csv_path}")

        else:
            csv_path = None

if __name__ == "__main__":
    user_query = "Create a line plot of temperature over time from the data in the csv file."
    shared_folder = r"C:\Users\soundarya.sarathi\OneDrive - Accenture\study_materials\PROJECTS\MCP_AGENTIC_AI\static\1\21\1"
    csv_filename = "environmental_data.csv"
    execute_plotting_agent(user_query, shared_folder, csv_filename)