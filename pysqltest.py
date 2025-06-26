
import pyodbc

server = 'einnelindiadevelopment.cmbmhqnd5eet.us-east-2.rds.amazonaws.com'
database = 'TaskAssigner'
username = 'EinNel_training'
password = 'EinNeltraining2023!'
driver = '{ODBC Driver 18 for SQL Server}'

conn = pyodbc.connect(
    f'DRIVER={driver};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
    f'TrustServerCertificate=yes;'
    f'Encrypt=yes;'
    f'PORT=1433'
)

cursor = conn.cursor()
# cursor.execute("SELECT DB_NAME();")
# row = cursor.fetchone()
# print("Connected to database:", row[0])
#
# # ✅ Get all table names in the current database
# cursor.execute("""
#     SELECT TABLE_NAME
#     FROM INFORMATION_SCHEMA.TABLES
#     WHERE TABLE_TYPE = 'BASE TABLE';
# """)
#
# tables = cursor.fetchall()
#
# print("Tables in database:")
# for table in tables:
#     print(table[0])
#
# # ---- Columns ----
# cursor.execute("""
#     SELECT COLUMN_NAME
#     FROM INFORMATION_SCHEMA.COLUMNS
#     WHERE TABLE_NAME = 'User';
# """)
# user_columns = [row[0] for row in cursor.fetchall()]
# print("User table columns:", user_columns)
#
# # ---- First 10 rows ----
# cursor.execute("""
#     SELECT TOP 10 * FROM [User];
# """)
# user_rows = cursor.fetchall()
# print("First 10 rows in User table:")
# for row in user_rows:
#     print(row)
#
#
# # ---- Columns ----
# cursor.execute("""
#     SELECT COLUMN_NAME
#     FROM INFORMATION_SCHEMA.COLUMNS
#     WHERE TABLE_NAME = 'Task';
# """)
# task_columns = [row[0] for row in cursor.fetchall()]
# print("Task table columns:", task_columns)
#
# # ---- First 10 rows ----
# cursor.execute("""
#     SELECT TOP 10 * FROM Task;
# """)
# task_rows = cursor.fetchall()
# print("First 10 rows in Task table:")
# for row in task_rows:
#     print(row)
#
# cursor.close()
# conn.close()
cursor.execute("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE';
""")
tables = [row[0] for row in cursor.fetchall()]
print("Tables found:", tables)

# 2️⃣ For each table, get its columns:
for table in tables:
    cursor.execute(f"""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{table}';
    """)
    columns = [row[0] for row in cursor.fetchall()]
    print(f"\n✅ Table: [{table}]")
    print("Columns:", columns)