from sentence_transformers import SentenceTransformer


model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")


def get_embeddings(texts: list[str]):
    embedding = model.encode(texts, convert_to_numpy= True).tolist()
    return embedding
