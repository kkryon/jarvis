from sentence_transformers import SentenceTransformer
import numpy as np

# It's good practice to load the model once and reuse it.
# We can specify a model name or let it use a default.
# Using a smaller, efficient model can be good for local development.
# 'all-MiniLM-L6-v2' is a popular choice for good balance of speed and quality.
DEFAULT_EMBEDDING_MODEL = 'all-MiniLM-L6-v2' 
# For more powerful embeddings, consider models like 'all-mpnet-base-v2'
# or models from the SBERT.net documentation.

MODEL_INSTANCE = None

def get_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL) -> SentenceTransformer:
    """
    Loads and returns a SentenceTransformer model.
    Caches the model instance for efficiency.
    """
    global MODEL_INSTANCE
    if MODEL_INSTANCE is None or MODEL_INSTANCE.model_name != model_name:
        try:
            MODEL_INSTANCE = SentenceTransformer(model_name)
            # You might want to move the model to a specific device if using GPU
            # if torch.cuda.is_available():
            #     MODEL_INSTANCE = MODEL_INSTANCE.to(torch.device("cuda"))
            print(f"Embedding model '{model_name}' loaded successfully.")
        except Exception as e:
            print(f"Error loading sentence transformer model '{model_name}': {e}")
            # Fallback or raise error
            raise
    return MODEL_INSTANCE

def generate_embedding(text: str | list[str], model_name: str = DEFAULT_EMBEDDING_MODEL) -> np.ndarray | list[np.ndarray] | None:
    """
    Generates an embedding for a given text or list of texts.

    Args:
        text: A single string or a list of strings to embed.
        model_name: The name of the SentenceTransformer model to use.

    Returns:
        A numpy array representing the embedding (or list of arrays if input is list), 
        or None if an error occurs.
    """
    try:
        model = get_embedding_model(model_name)
        # The encode method can take a single string or a list of strings.
        # It returns a numpy array or a list of numpy arrays.
        embeddings = model.encode(text, convert_to_numpy=True)
        return embeddings
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def generate_embeddings_batched(texts: list[str], model_name: str = DEFAULT_EMBEDDING_MODEL, batch_size: int = 32) -> list[np.ndarray] | None:
    """
    Generates embeddings for a list of texts in batches.

    Args:
        texts: A list of strings to embed.
        model_name: The name of the SentenceTransformer model to use.
        batch_size: The number of texts to process in each batch.

    Returns:
        A list of numpy arrays representing the embeddings, 
        or None if an error occurs.
    """
    try:
        model = get_embedding_model(model_name)
        # Use model.encode with batch_size for potentially better performance on large lists
        all_embeddings = model.encode(texts, batch_size=batch_size, convert_to_numpy=True)
        return [emb for emb in all_embeddings] # Ensure it's a list of arrays
    except Exception as e:
        print(f"Error generating embeddings in batch: {e}")
        return None

if __name__ == '__main__':
    print("Testing Embedding Utils...")

    # Test 1: Simple embedding
    test_text_1 = "This is a test sentence for embedding."
    embedding_1 = generate_embedding(test_text_1)
    if embedding_1 is not None:
        print(f"\nEmbedding for '{test_text_1}':")
        print(f"Shape: {embedding_1.shape}") # (384,) for all-MiniLM-L6-v2
        # print(f"Sample values: {embedding_1[:5]}...")
    else:
        print(f"Failed to generate embedding for '{test_text_1}'.")

    # Test 2: Embedding a list of sentences
    test_texts_list = [
        "The quick brown fox jumps over the lazy dog.",
        "Exploring the universe and its mysteries.",
        "AI is transforming the world.",
        "Sentence embeddings are useful for semantic search."
    ]
    embeddings_list = generate_embedding(test_texts_list)
    if embeddings_list is not None:
        print(f"\nEmbeddings for list of sentences:")
        print(f"Number of embeddings: {len(embeddings_list)}")
        if len(embeddings_list) > 0:
            print(f"Shape of first embedding: {embeddings_list[0].shape}")
            # print(f"Sample of first embedding: {embeddings_list[0][:5]}...")
    else:
        print("Failed to generate embeddings for the list of sentences.")

    # Test 3: Batched embedding
    # Creating a slightly larger list for batch testing
    test_texts_batch = [f"Sentence number {i}" for i in range(50)] 
    embeddings_batch = generate_embeddings_batched(test_texts_batch, batch_size=16)
    if embeddings_batch is not None:
        print(f"\nBatched embeddings:")
        print(f"Number of embeddings: {len(embeddings_batch)}")
        if len(embeddings_batch) > 0:
            print(f"Shape of first batched embedding: {embeddings_batch[0].shape}")
    else:
        print("Failed to generate batched embeddings.")
    
    # Test 4: Using a different model (if available and desired for testing)
    # Note: This will download the model if not already cached by sentence-transformers
    # try:
    #     print("\n--- Testing with a different model (paraphrase-MiniLM-L3-v2) ---")
    #     test_text_alt_model = "Another sentence for a different model."
    #     embedding_alt_model = generate_embedding(test_text_alt_model, model_name='paraphrase-MiniLM-L3-v2')
    #     if embedding_alt_model is not None:
    #         print(f"Embedding for '{test_text_alt_model}' using paraphrase-MiniLM-L3-v2:")
    #         print(f"Shape: {embedding_alt_model.shape}")
    #     else:
    #         print("Failed to generate embedding with alternative model.")
    # except Exception as e:
    #     print(f"Could not test alternative model (perhaps not installed or network issue): {e}")


    print("\nEmbedding Utils test complete.") 