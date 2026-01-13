from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    return "TradeSense Al Platform is Running!"

@app.route('/test')
def test():
    return "Server is accessible!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)