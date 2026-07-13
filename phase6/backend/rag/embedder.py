import os
from openai import OpenAI
from dotenv import load_dotenv
import math

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))   

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Measures how similar two embeddings are.
    Returns a number between -1 and 1.
    Closer to 1 = more similar meaning.
    """
    # Dot product — multiply corresponding numbers and sum them
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Magnitude of each vector — like finding the "length"
    magnitude1  = math.sqrt(sum(a * a for a in vec1))
    magnitude2  = math.sqrt(sum(b * b for b in vec2))
    
    # Cosine similarity formula
    return dot_product / (magnitude1 * magnitude2)

def get_embedding(text: str) -> list[float]:
    text = text.replace("\n", " ").strip()
    
    response = client.embeddings.create(
        input = text,
        model = "text-embedding-3-small"
    )
    
    return response.data[0].embedding

if __name__ == "__main__":
    print("Getting embeddings...\n")
    
    test1 = "SharePoint SPFx React developer TypeScript"
    test2 = "SPFx engineer React TypeScript web parts"
    test3 = "Java Spring Boot backend developer"
    
    emb1 = get_embedding(test1)
    emb2 = get_embedding(test2)
    emb3 = get_embedding(test3)
    
    print(f"Embedding dimensions: {len(emb1)}\n")
    
    # Now measure similarity between all pairs
    sim_1_2 = cosine_similarity(emb1, emb2)
    sim_1_3 = cosine_similarity(emb1, emb3)
    sim_2_3 = cosine_similarity(emb2, emb3)
    
    print("Similarity scores:")
    print(f"  SharePoint React  vs  SPFx TypeScript  : {sim_1_2:.4f}")
    print(f"  SharePoint React  vs  Java Spring Boot : {sim_1_3:.4f}")
    print(f"  SPFx TypeScript   vs  Java Spring Boot : {sim_2_3:.4f}")
    
    print("\nWhat this means:")
    print(f"  SharePoint vs SPFx : {'similar ✅' if sim_1_2 > 0.8 else 'different ❌'}")
    print(f"  SharePoint vs Java : {'similar ✅' if sim_1_3 > 0.8 else 'different ❌'}")