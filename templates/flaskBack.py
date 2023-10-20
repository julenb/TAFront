from flask import Flask, request, jsonify



events =[]

with open('.aws/credentials') as f:
    lines = f.readlines()

for line in lines:
    name = line.split('-')[0]
    number = int(line.split('-')[1])
    events.append({'nombre':name, 'entradas':number})


app = Flask(__name__)
@app.route('/getEvents', methods=['GET'])
def getEvents():  
    return jsonify(events)

@app.route('/getCerts', methods=['GET'])
def getCerts():
    with open('.aws/credentials') as f:
        lines = f.readlines()
        ACCESS_KEY = str(lines[2].split("=")[1]).strip()
        KEY_ID = str(lines[1].split("=")[1]).strip()
        TOKEN = str(lines[3].split("=")[1]).strip()
    return {'access_key': ACCESS_KEY, 'key_id': KEY_ID, 'token':TOKEN}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000)