from app.models.author import Author
from app.schemas.author_schema import AuthorSchema
from app.extensions import db

def demonstrate_author_serialization():
    # Simulate database query
    print("1. Raw Database Query:")
    authors = Author.query.all()
    for author in authors:
        print(f"Raw Author Object: {author}")
        print(f"  - Type: {type(author)}")
        print(f"  - Attributes: {dir(author)}\n")

    # Serialize authors
    print("2. Serialization Process:")
    author_schema = AuthorSchema(many=True)
    serialized_authors = author_schema.dump(authors)
    
    print("Serialized Authors:")
    import json
    print(json.dumps(serialized_authors, indent=2))

# Note: This is a demonstration script
# It requires a proper Flask application context to run
if __name__ == '__main__':
    demonstrate_author_serialization()
