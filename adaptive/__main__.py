# Importing local modules and packages
from adaptive import create_app

# Importing libraries to load the environment variables
from dotenv import load_dotenv
from os import getenv
from sys import platform
from multiprocessing import set_start_method

app = create_app()

if __name__ == "__main__":
    # Defining the proper method to spawn processes depending on the platform
    if platform == "darwin":
        set_start_method("fork", force=True)
    else:
        set_start_method("spawn", force=True)

    # Getting the environment variables
    load_dotenv(dotenv_path=".env")

    app.run(debug=True, host="0.0.0.0", port=getenv("WEB_SERVER_PORT"))
