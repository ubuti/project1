import os
import mariadb
from datetime import datetime  # Changed import for cleaner code usage

# --- Configuration ---

# Directory to scan for files
directory = "/home/inuit/project1/cameraimg"

# MariaDB connection configuration
db_config = {
    "user": "inuit",
    "password": "klabautermann",
    "host": "localhost",
    "database": "cam_db"
}

# --- Main Program ---

try:
    # Connect to the MariaDB database
    conn = mariadb.connect(**db_config)
    cursor = conn.cursor()
except mariadb.Error as e:
    print(f"Error connecting to MariaDB: {e}")
    exit(1)

# Loop over all files in the given directory
for orig_filename in os.listdir(directory):
    file_path = os.path.join(directory, orig_filename)
    if not os.path.isfile(file_path):
        continue  # Skip if not a file

    # Remove the first 9 characters to isolate the datetime part,
    # then remove the file extension.
    trimmed_filename = orig_filename[9:]
    name_without_ext, _ = os.path.splitext(trimmed_filename)

    # Attempt to parse the date and time from the filename
    try:
        file_datetime = datetime.strptime(name_without_ext, '%Y-%m-%d_%H-%M-%S')
    except ValueError:
        # Skip files that do not match the required format
        continue

    # Derive a table name based on the date extracted from the file
    table_name = f"files_{file_datetime.strftime('%Y_%m_%d')}"

    # Create table if it does not exist; note that the 'created_at' column is now TIME only.
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        id INT AUTO_INCREMENT PRIMARY KEY,
        path VARCHAR(255) NOT NULL,
        created_at TIME NOT NULL
    );
    """
    try:
        cursor.execute(create_table_sql)
    except mariadb.Error as e:
        print(f"Error creating table {table_name}: {e}")
        continue

    # Insert the file's absolute path and the extracted time (HH:MM:SS) into the table
    insert_sql = f"INSERT INTO `{table_name}` (path, created_at) VALUES (?, ?)"
    file_time = file_datetime.strftime('%H:%M:%S')
    try:
        cursor.execute(insert_sql, (os.path.abspath(file_path), file_time))
        conn.commit()
        print(f"Inserted file: {file_path} into table: {table_name}")
    except mariadb.Error as e:
        print(f"Error inserting data into {table_name}: {e}")

# Clean up database connection
cursor.close()
conn.close()
