from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import environ
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import FireCrawlLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, OpenAI
from django.conf import settings

# Load environment variables from .env
env = environ.Env()
environ.Env.read_env()

# Define the persistent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(current_dir, "db")
persistent_directory = os.path.join(db_dir, "chroma_db_firecrawl")

def create_vector_store():
    # Crawl the website and create a vector store if it doesn't exist
    api_key = settings.FIRECRAWL_API_KEY
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY environment variable not set")

    loader = FireCrawlLoader(api_key=api_key, url="https://hotbotstudios.com/", mode="scrape")
    docs = loader.load()

    for doc in docs:
        for key, value in doc.metadata.items():
            if isinstance(value, list):
                doc.metadata[key] = ", ".join(map(str, value))

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    split_docs = text_splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY)
    db = Chroma.from_documents(split_docs, embeddings, persist_directory=persistent_directory)

if not os.path.exists(persistent_directory):
    create_vector_store()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY)
db = Chroma(persist_directory=persistent_directory, embedding_function=embeddings)
openai_model = OpenAI(api_key=settings.OPENAI_API_KEY)

def query_vector_store(query):
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    relevant_docs = retriever.invoke(query)

    if not relevant_docs or all(not doc.page_content.strip() for doc in relevant_docs):
        return "I do not know."

    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    prompt = (f"Context:\n{context}\n\n"
              f"Based on the above context, answer the following question. "
              f"If the answer is not found in the context, respond with 'I do not know.'\n\n"
              f"Query: {query}\n\n"
              f"Response:")

    response = openai_model.generate(prompts=[prompt], max_tokens=150)
    generated_text = response.generations[0][0].text
    return generated_text

class QueryView(APIView):
    def post(self, request):
        query = request.data.get("query")
        if not query:
            return Response({"error": "Query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        response = query_vector_store(query)
        return Response({"response": response})

