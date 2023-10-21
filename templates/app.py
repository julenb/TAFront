from flask import Flask, request, jsonify
import boto3
import os

app = Flask(__name__)
queue_url = 'https://sqs.us-east-1.amazonaws.com/252400710903/requestTA'  # Reemplaza con la URL de tu cola SQS
with open('.aws/credentials') as f:
    lines = f.readlines()
ACCESS_KEY = str(lines[2].split("=")[1]).strip()
KEY_ID = str(lines[1].split("=")[1]).strip()
TOKEN = str(lines[3].split("=")[1]).strip()


print(KEY_ID)
print(ACCESS_KEY)
print(TOKEN)


# Configura el cliente de SQS
sqs = boto3.client(
    'sqs',
    region_name='us-east-1',
    aws_access_key_id= KEY_ID,
    aws_secret_access_key= ACCESS_KEY,
    aws_session_token=  TOKEN
    )  


@app.route('/listen', methods=['GET'])
def listen_to_sqs():
    try:
        # Recibe el mensaje de SQS
        message = sqs.receive_message(QueueUrl=queue_url, AttributeNames=['All'], MaxNumberOfMessages=1, WaitTimeSeconds=20)

        if 'Messages' in message:
            # Procesa el mensaje
            message_body = message['Messages'][0]['Body']
            
            # Aquí puedes agregar la lógica para procesar el mensaje recibido
            
            # Elimina el mensaje de la cola
            receipt_handle = message['Messages'][0]['ReceiptHandle']
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

            return jsonify({'message': message['Messages'][0]['Body']})
        else:
            return jsonify({'message': 'No se encontraron mensajes en la cola SQS'})

    except Exception as e:
        return jsonify({'error': str(e)})
    

@app.route('/send', methods=['GET'])
def send_to_sqs():
    try:
        # Obtén el mensaje que deseas enviar desde la solicitud POST
        # message_body = request.json.get('message')
        message_body = """{"name":"Evento 1","number":4,"uuid":"iujhiuhihihu"}"""

        # Envía el mensaje a la cola SQS
        response = sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)

        return jsonify({'message': 'Mensaje enviado a la cola SQS exitosamente', 'message_id': response['MessageId']})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
