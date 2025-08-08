from app.services.tagging import TaggingService

tagger = TaggingService()

texts = [
    "OpenAI released a new model for developers.",
    "COVID-19 vaccines are being distributed globally."
]
domain_dict = ["AI", "vaccine"]
language = "en"

results = tagger.tag_texts(texts, language=language, domain_dict=domain_dict)

for result in results:
    print(f"\nText: {result.text}\nTags: {result.tags}\nLanguage: {result.language}")
