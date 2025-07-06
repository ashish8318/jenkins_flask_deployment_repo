# app.py
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    # return "Hello from Flask on Kubernetes!"
    return "<h1>****** Welcome to ARGOCD *****"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
