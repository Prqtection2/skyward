from flask import Flask, render_template, request, jsonify
from utils.skyward import SkywardGPA
import os

app = Flask(__name__)
app.config['ENV'] = os.environ.get('FLASK_ENV', 'production')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        calculator = SkywardGPA(username, password)
        result = calculator.calculate()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)