from app import create_app  # your Flask factory function
from mangum import Mangum  # serverless adapter

app = create_app()  # Flask app

# Wrap Flask app with Mangum for serverless deployment
handler = Mangum(app)
