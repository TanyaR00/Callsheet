import clickhouse_connect

def verify():
    print("Connecting to ClickHouse...")
    try:
        client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    except Exception as e:
        print(f"Failed to connect to ClickHouse. Ensure it is running locally or update the credentials. Error: {e}")
        return
    
    row_count = client.command("SELECT count() FROM scene_cost_history")
    print(f"\nTotal rows in scene_cost_history: {row_count}")
    
    print("\n--- Sample Query: Average Cost by Time of Day ---")
    result = client.query("SELECT time_of_day, avg(actual_cost) as avg_cost, count() as cnt FROM scene_cost_history GROUP BY time_of_day ORDER BY avg_cost DESC")
    
    for row in result.named_results():
        print(f"Time: {row['time_of_day']:<12} | Avg Cost: ${row['avg_cost']:,.2f} | Count: {row['cnt']}")

if __name__ == '__main__':
    verify()
