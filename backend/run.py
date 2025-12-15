from backend.app import create_app

app = create_app()

# Local dev only
if __name__ == "__main__":
    app.run(debug=True)
