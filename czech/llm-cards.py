from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.rate_limiters import InMemoryRateLimiter

with open("czech/google-genai.apikey") as f:
    apikey = f.read()

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.1,  # <-- Super slow! We can only make a request once every 10 seconds!!
    check_every_n_seconds=0.1,  # Wake up every 100 ms to check whether allowed to make a request,
    max_bucket_size=10,  # Controls the maximum burst size.
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", api_key=apikey, rate_limiter=rate_limiter
)

# Simple text invocation
result = llm.invoke("Sing a ballad of LangChain.")
print(result.content)
