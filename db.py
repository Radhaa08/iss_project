import os
import psycopg2

conn = psycopg2.connect("postgresql://radha:T-6zxK6IsKE61zXRI4-I3Q@newcluster-8912.8nk.gcp-asia-southeast1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full")

with conn.cursor() as cur:
    cur.execute("SELECT now()")
    res = cur.fetchall()
    conn.commit()
    print(res)