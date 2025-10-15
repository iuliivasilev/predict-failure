import os
from flask import Flask, render_template, redirect, send_file
from flask import request, session
from flask import url_for, jsonify

from core.system_manager import SystemManager

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.secret_key = 'your_secret_key'  # Для работы сессии

manager = SystemManager()

@app.route('/')
def main():
    # return render_template('index.html', header={})
    result = manager.find_objects()
    print(result)
    data = manager.collect_data('cpu')
    return render_template('index.html', collectors=result)

@app.route('/find_objects')
def find_objects():
    result = manager.find_objects()
    return render_template('index.html', collectors=result)

@app.route('/system_status')
def system_status():
    status = {}
    for name, collector in manager.collectors.items():
        try:
            df = collector.collect()
            if not df.empty:
                status[name] = df.iloc[0].to_dict()
        except Exception as e:
            status[name] = {"error": str(e)}
    return render_template('system_status.html', status=status)


if __name__ == '__main__':
    app.run(debug=True, threaded=False, host='0.0.0.0', port=11111)