import os
from langchain_openai import OpenAIEmbeddings
import traceback

# Load the OpenAI API key from environment variables
openai_api = os.environ.get("OPENAI_API_KEY")

# Debugging the API key
if not openai_api:
    print("❌ API key is missing! Make sure OPENAI_API_KEY is set in your environment.")
else:
    print(f"✅ API key loaded: {openai_api[:5]}...")  # Print the first few characters of the key

def get_embedding(text: str, model: str = "text-embedding-ada-002"):
    """Get OpenAI embedding for a single text string"""
    try:
        print(f"🔍 Generating embedding for: {text}")
        embedding_model = OpenAIEmbeddings(
            model=model,
            api_key=openai_api,
            base_url="https://warranty-api-dev.picontechnology.com:8443",
        )
        embedding = embedding_model.embed_query(text)
        if embedding is None:
            print("❌ Embedding generation failed: No embedding returned.")
            return
        print(f"✅ Embedding generated successfully! Length: {len(embedding)}")
        return embedding
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        traceback.print_exc()
        raise e

# # Get input from the user
# user_input = input("Enter text to embed: ")

# # Generate the embedding
# try:
#     embedding = get_embedding(user_input)
#     if embedding:
#         print(f"✅ Embedding generated! Length: {len(embedding)}")
#         print(f"First 5 values of the embedding: {embedding[:5]}")
# except Exception as e:
#     print(f"❌ Failed to generate embedding: {e}")
