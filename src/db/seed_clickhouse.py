import os
import random
import uuid
import clickhouse_connect
from google import genai
import time

# Note: This synthetic data is purely illustrative and meant to demonstrate
# ClickHouse's hybrid analytical (OLAP) + Vector Search capability.

def generate_synthetic_data(num_records=300):
    # Initialize genai client. Assumes GEMINI_API_KEY is available in the environment if needed
    client = genai.Client()
    
    locations = ["COFFEE SHOP", "STREET", "APARTMENT", "WAREHOUSE", "SPACE STATION", "FOREST", "DESERT", "MANSION"]
    times = ["DAY", "NIGHT", "DUSK", "DAWN", "CONTINUOUS"]
    int_exts = ["INT", "EXT", "INT/EXT"]
    
    records = []
    descriptions = []
    
    for _ in range(num_records):
        int_ext = random.choice(int_exts)
        time_of_day = random.choice(times)
        cast_count = random.randint(0, 15)
        vfx_density = random.uniform(0.0, 0.25)
        location_type = random.choice(locations)
        
        is_night_ext = 1 if int_ext == 'EXT' and time_of_day == 'NIGHT' else 0
        random_variance = random.uniform(-10000, 20000)
        
        # Base cost formula provided
        base_cost = 15000 + (cast_count * 4500) + (vfx_density * 80000) + (is_night_ext * 25000) + random_variance
        
        # Ensure cost is minimally realistic
        base_cost = max(base_cost, 5000)
        
        shoot_duration_hours = base_cost / 15000.0 + random.uniform(2, 6)
        
        desc = f"A {int_ext} scene at a {location_type} during {time_of_day} with {cast_count} characters. VFX density score is {vfx_density:.2f}."
        descriptions.append(desc)
        
        records.append({
            'scene_comp_id': uuid.uuid4(),
            'int_ext': int_ext,
            'time_of_day': time_of_day,
            'cast_count': cast_count,
            'vfx_density': vfx_density,
            'location_type': location_type,
            'actual_cost': base_cost,
            'shoot_duration_hours': shoot_duration_hours
        })
        
    print("Generating embeddings via google-genai (text-embedding-004)...")
    
    # Batch processing to respect API limits
    batch_size = 50
    all_embeddings = []
    for i in range(0, len(descriptions), batch_size):
        batch_descs = descriptions[i:i+batch_size]
        response = client.models.embed_content(
            model='text-embedding-004',
            contents=batch_descs
        )
        for emb in response.embeddings:
            all_embeddings.append(emb.values)
        time.sleep(1) # Simple rate-limit spacing
        
    for i, record in enumerate(records):
        record['feature_vector'] = all_embeddings[i]
        
    return records

def seed_db():
    print("Connecting to ClickHouse...")
    # Update these connection details as needed for your ClickHouse cluster
    try:
        client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    except Exception as e:
        print(f"Failed to connect to ClickHouse. Ensure it is running locally or update the credentials. Error: {e}")
        return
    
    print("Creating table from schema.sql...")
    with open('src/db/schema.sql', 'r') as f:
        schema = f.read()
    client.command(schema)
    
    print("Generating illustrative data...")
    records = generate_synthetic_data(300)
    
    print("Inserting records into scene_cost_history...")
    data = [[
        r['scene_comp_id'],
        r['int_ext'],
        r['time_of_day'],
        r['cast_count'],
        r['vfx_density'],
        r['location_type'],
        r['actual_cost'],
        r['shoot_duration_hours'],
        r['feature_vector']
    ] for r in records]
    
    client.insert('scene_cost_history', data, column_names=[
        'scene_comp_id', 'int_ext', 'time_of_day', 'cast_count', 'vfx_density',
        'location_type', 'actual_cost', 'shoot_duration_hours', 'feature_vector'
    ])
    
    print("Seeding complete! Successfully inserted 300 records.")

if __name__ == '__main__':
    seed_db()
