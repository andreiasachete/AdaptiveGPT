# Importing local modules and packages
from adaptive import create_app

# Importing libraries to load the environment variables
from dotenv import load_dotenv
from os import getenv

app = create_app()

if __name__ == "__main__":
    # Getting the environment variables
    load_dotenv(dotenv_path=".env")

    app.run(debug=True, host="0.0.0.0", port=getenv("WEB_SERVER_PORT"))
