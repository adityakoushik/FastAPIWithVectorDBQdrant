from fastapi import FastAPI
from backend.db.qdrant import qdrant_client
from backend.services.embedding_service import create_embedding
from qdrant_client.models import Distance, VectorParams, PointStruct

# Now here creating object of FastAPI class
app = FastAPI(
    title="IntelliDocs API",
    description="AI-powered document knowledge base using Vector Database",
    version="1.0.0",
)

@app.get("/")
def root():
    return {
        "message": "IntelliDocs API is running"
    }


@app.get("/embeddings/test")
def test_embedding():
    text = "Employees get 12 casual leaves per year."
    vector = create_embedding(text)

    return {
        "text": text,
        "vector_size": len(vector),
        "vector_preview": vector[:5],
    }
    
@app.get("/health")
def health_check():
    # Here we are checking the health of Qdrant Database by getting the collections from it.
    collections = qdrant_client.get_collections()
    return {
        "status": "healthy",
        "qdrant": "connected",
        "collections": len(collections.collections)
    }
    
@app.get("/collections")
def get_collections():
    collections = qdrant_client.get_collections()
    
    # collections_name = []
    # for collection in collections.collections:
    #     collections_name.append(collection.name)
    # return {
    #     "collections": collections_name
    # }
    
    # Now Using list comprehension in python to get the collections name from the collections object.
    return{
        "collections" : [
            collection.name for collection in collections.collections
        ]
    }
    
@app.post("/collections/documents")
def create_documents_collection():
    qdrant_client.create_collection(
        collection_name="documents",
        # VectorParams is decided that how the collection of vectors will be stored in the Qdrant database. It has two parameters size and distance. 
        # Size is the dimension of the vector which is 3 , means accept only 3 dimensional vector in the collection i.e. [0.2, 0.5, 0.9]
        # and distance is the distance metric used to calculate the similarity between vectors.
        # And Similarity method = Cosine, so its Cosine similarity/distance based search
        vectors_config = VectorParams(
            size = 3,
            distance = Distance.COSINE
        )
    )
    return {
        "message": "Documents collection created successfully"
    }

@app.post("/documents/seed")
def seed_documents():
    # points resembles the data that we want to insert into the Qdrant collection. Each point is represented as a PointStruct object, which contains an id, a vector, and optional payload data.
    points = [
        # these vectors are 3 dimensional manual vector for learning purpose, in real world we will use embedding model to get the vector representation of the text.
        PointStruct(
            id=1,
            vector=[1.0, 0.0, 0.0],
            payload={
                "text": "Employees get 12 casual leaves per year."
            }
        ),
        PointStruct(
            id=2,
            vector=[0.0, 1.0, 0.0],
            payload={
                "text": "Docker packages applications into containers."
            }
        ),
        PointStruct(
            id=3,
            vector=[0.0, 0.0, 1.0],
            payload={
                "text": "React is used for building user interfaces."
            }
        ),
    ]
    # upsert is responsible for inserting or updating the points in the Qdrant collection. If a point with the same id already exists, it will be updated; otherwise, a new point will be inserted.
    qdrant_client.upsert(
        collection_name="documents",
        points=points
    )
    
    return {
        "message": "Documents inserted successfully"
    }
    
@app.get("/documents/search")
def search_documents():
    # Example query vector for searching
    # Stored: [1.0, 0.0, 0.0]
    # Query : [0.9, 0.1, 0.0]
    query_vector = [0.9, 0.1, 0.0]
    
    # This below means Qdrant, find the points most similar to this query vector.
    results = qdrant_client.query_points(
        collection_name="documents",
        # query_vector = This means Qdrant will compare this vector with the stored vectors.
        query=query_vector,
        limit=3
    )
    
    return {
        # "results": [
        #     {
        #         "id": point.id,
        #         "score": point.score,
        #         "payload": point.payload
        #     }
        #     for point in results.points
        # ]
        "results": [
            {
                "id": point.id,
                "score": point.score,
                "payload": point.payload
            }
            for point in results.points
        ]
    }
