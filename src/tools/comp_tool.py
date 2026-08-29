from typing import Dict, Any
from google import genai
import clickhouse_connect

def query_scene_comps(scene_description: str, int_ext: str, cast_count: int, top_k: int = 5, ch_host: str = 'localhost', ch_port: int = 8123) -> Dict[str, Any]:
    """
    Finds historical scene cost comps using vector similarity and analytical aggregations.
    
    Args:
        scene_description (str): A natural language description of the scene.
        int_ext (str): The scene setting ('INT', 'EXT', or 'INT/EXT').
        cast_count (int): The number of characters in the scene.
        top_k (int, optional): The number of nearest neighbors to consider. Defaults to 5.
        ch_host (str, optional): ClickHouse host. Defaults to 'localhost'.
        ch_port (int, optional): ClickHouse port. Defaults to 8123.
        
    Returns:
        dict: A dictionary containing cost estimates (p10, median, p90, avg, stddev) and a confidence indicator.
    """
    # Generate embedding
    client = genai.Client()
    response = client.models.embed_content(
        model='text-embedding-004',
        contents=scene_description
    )
    query_vector = response.embeddings[0].values
    
    # Connect to ClickHouse
    try:
        ch_client = clickhouse_connect.get_client(host=ch_host, port=ch_port, username='default', password='')
    except Exception as e:
        return {"error": f"Failed to connect to ClickHouse: {str(e)}"}
        
    query = """
    SELECT 
        quantile(0.1)(actual_cost) as p10_cost,
        quantile(0.5)(actual_cost) as median_cost,
        quantile(0.9)(actual_cost) as p90_cost,
        avg(actual_cost) as avg_cost,
        stddevPop(actual_cost) as cost_stddev,
        count() as comp_count
    FROM (
        SELECT actual_cost, cosineDistance(feature_vector, {query_vec:Array(Float32)}) as dist
        FROM scene_cost_history
        WHERE int_ext = {int_ext:String} AND cast_count = {cast_count:UInt16}
        ORDER BY dist ASC
        LIMIT {top_k:UInt16}
    )
    """
    
    result = ch_client.query(query, parameters={
        'query_vec': query_vector,
        'int_ext': int_ext,
        'cast_count': cast_count,
        'top_k': top_k
    }).named_results()
    
    if not result or result[0].get('comp_count', 0) == 0:
        return {"error": "No comparable scenes found."}
        
    stats = result[0]
    avg_cost = stats.get('avg_cost', 0)
    cost_stddev = stats.get('cost_stddev', 0)
    
    # Determine confidence based on variance
    if avg_cost > 0 and (cost_stddev / avg_cost) > 0.40:
        confidence = "LOW (High Variance)"
    else:
        confidence = "HIGH"
        
    return {
        "p10_cost": float(stats.get('p10_cost', 0)),
        "median_cost": float(stats.get('median_cost', 0)),
        "p90_cost": float(stats.get('p90_cost', 0)),
        "avg_cost": float(avg_cost),
        "cost_stddev": float(cost_stddev),
        "comp_count": int(stats.get('comp_count', 0)),
        "confidence": confidence
    }
