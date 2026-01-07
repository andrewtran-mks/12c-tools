from app import create_app
from os import environ

app = create_app()

if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', '0.0.0.0')
    try:
        PORT = int(environ.get('SERVER_PORT', '5050'))
    except ValueError:
        PORT = 5050
    app.run(host=HOST, port=PORT, debug=True)