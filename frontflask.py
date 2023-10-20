from flask import Flask, request, jsonify,render_template, send_file,make_response, redirect, url_for
import boto3
import botocore
import json
import requests
import uuid


queue_url_request = 'https://sqs.us-east-1.amazonaws.com/252400710903/requestTA'
queue_url_response = 'https://sqs.us-east-1.amazonaws.com/252400710903/responseTA' # Reemplaza con la URL de tu cola SQS
with open('.aws/credentials') as f:
    lines = f.readlines()
ACCESS_KEY = str(lines[2].split("=")[1]).strip()
KEY_ID = str(lines[1].split("=")[1]).strip()
TOKEN = str(lines[3].split("=")[1]).strip()


# Configura el cliente de SQS
sqs = boto3.client(
    'sqs',
    region_name='us-east-1',
    aws_access_key_id= KEY_ID,
    aws_secret_access_key= ACCESS_KEY,
    aws_session_token=  TOKEN
    )  

dynamodb = boto3.client('dynamodb',
    region_name='us-east-1',
    aws_access_key_id= KEY_ID,
    aws_secret_access_key= ACCESS_KEY,
    aws_session_token=  TOKEN)

table_name = 'Eventos'






app = Flask(__name__)

@app.route('/')
def index():

    response = dynamodb.scan(TableName=table_name)
    items = response.get('Items', [])
    eventos = []

    for elemento in items:
        nombre = elemento['nombre']['S']
        eventos.append(nombre)


    print(items)
    print(eventos)
    return render_template('./index.html', eventos=eventos)

@app.route('/procesar_peticion', methods=['POST'])
def procesar_peticion():

    uid = str(uuid.uuid4()).replace('-','')
    evento = request.form['evento']
    entradas = int(request.form['entradas'])
    print(f"Evento: {evento}, Entradas: {entradas}")
    # Lógica para procesar el formulario aquí
    try:

        data = {
        "name": evento.replace(' ', '_'),
        "number": entradas,
        "uuid": uid
        }
        json_data = json.dumps(data)
        message_body = str(json_data)

        # Envía el mensaje a la cola SQS
        response = sqs.send_message(QueueUrl=queue_url_request, MessageBody=message_body)

        print('Send = ok')
        print(message_body)

         # ahora vamos a esperar en la otra cola

        while True:
            
            # Recibe mensajes de la cola
            messages = sqs.receive_message(QueueUrl=queue_url_response, AttributeNames=['All'], MaxNumberOfMessages=10, WaitTimeSeconds=20)
            print('mensaje recibido')
            if 'Messages' in messages:
                for message in messages['Messages']:
                    # Procesa el mensaje actual
                    message_body = message['Body']
                    print(message_body)
                    message_json = json.loads(message_body)

                    # Aquí puedes agregar la lógica para evaluar si deseas quedarte con el mensaje
                    if message_json['uuid'] == uid:
                        print(uid)
                        # Elimina el mensaje de la cola
                        receipt_handle = message['ReceiptHandle']
                        sqs.delete_message(QueueUrl=queue_url_response, ReceiptHandle=receipt_handle)

                        # Parseamos las respuestas correctas y no correctas
                        if message_json['message']=='Correct_Transaction':
                            #devolvemos un html con la id y la posibilidad de descargar un pdf con un boton
                            print('Todo bien')
                            return  redirect(url_for('procesar_peticion_pdf', key= message_json['archivo']))
                            
                        elif message_json['message']=='Sold_Out':
                            #devolvemos un html con el error y la opcioon de volver atras
                            print('No quedan entradas')
                        elif message_json['message']=='No_Exists_Event':
                            print('No disponible el evento seleccionado')
                        else: print('HAy un error en el sistema')





                        return jsonify(message_json)

    except Exception as e:
        return jsonify({'error': str(e)})
    


@app.route('/pdf', methods=['GET'])
def procesar_peticion_pdf():
    key = request.args.get('key', '')
    return render_template('./descargapdf.html',valor = key)



@app.route('/pdfdownload', methods=['GET'])
def descargarPDF():
    file_key = request.args.get('key', '')
    s3 = boto3.client('s3',
    region_name='us-east-1',
    aws_access_key_id= KEY_ID,
    aws_secret_access_key= ACCESS_KEY,
    aws_session_token=  TOKEN)

    # Nombre de tu bucket de S3
    bucket_name = 'repositorioticketsta'
    pdf_local_file = file_key.split('/')[1]
    print(pdf_local_file)
    
    response = s3.get_object(Bucket=bucket_name, Key=file_key)
    pdf_data = response['Body'].read()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename={file_key}'  # Cambia el nombre de descarga si lo deseas
    return response



@app.route('/createEvent', methods=['GET', 'POST'])
def createEvent():
    if request.method == 'POST':
        # Obtén los datos del formulario
        nombre = request.form['nombre']
        entradas_max = request.form['entradas_max']
        fecha = request.form['fecha']
        lugar = request.form['lugar']
        hora = request.form['hora']
        duracion = request.form['duracion']
        precio = request.form['precio']


        # Inserta los datos en DynamoDB
        item = {
            'nombre':{'S':nombre},
            'entradas_max':{'N':entradas_max},
            'fecha':{'S':fecha},
            'lugar':{'S':lugar},
            'hora':{'S':hora},
            'duracion':{'N':duracion},
            'precio':{'N':precio},
        }
        dynamodb.put_item(TableName=table_name, Item=item)

        # Redirige a la página principal después de crear el evento
        return redirect(url_for('index'))

    # Lee todos los elementos de la tabla DynamoDB
    response = dynamodb.scan(TableName=table_name)
    items = response.get('Items', [])

    return render_template('createEvents.html', items=items)




if __name__ == '__main__':
    app.run(debug=True, host='172.31.34.78',port=7000)




