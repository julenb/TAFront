import boto3
import json
import os
import creapdfs as CreaPDF
import uuid


queue_url_request = 'https://sqs.us-east-1.amazonaws.com/252400710903/requestTA'
queue_url_response = 'https://sqs.us-east-1.amazonaws.com/252400710903/responseTA'

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

print(TOKEN)

dynamodb = boto3.client('dynamodb',
    region_name='us-east-1',
    aws_access_key_id= KEY_ID,
    aws_secret_access_key= ACCESS_KEY,
    aws_session_token=  TOKEN)




#configuramos base de datos

s3 = boto3.client('s3',
    region_name='us-east-1',
    aws_access_key_id= KEY_ID,
    aws_secret_access_key= ACCESS_KEY,
    aws_session_token=  TOKEN)

# Nombre de tu bucket de S3
bucket_name = 'repositorioticketsta'





events =[]

with open('.aws/events') as f:
    lines = f.readlines()

for line in lines:
    name = line.split('-')[0]
    number = int(line.split('-')[1])
    events.append({'nombre':line.split('-')[0], 'entradas':int(line.split('-')[1]),'fecha':line.split('-')[2],'lugar':line.split('-')[3],'hora':line.split('-')[4],'duracion':line.split('-')[5],'precio':line.split('-')[6]})


def subir_pdf(local_file, bucket, s3_file):
    print(local_file+' '+bucket+' '+s3_file)
    s3 = boto3.client('s3', aws_access_key_id=KEY_ID,
                      aws_secret_access_key=ACCESS_KEY,
                      aws_session_token=TOKEN)

    try:
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    
def contar_entradas(carpeta):
    s3 = boto3.client('s3', aws_access_key_id=KEY_ID,
                      aws_secret_access_key=ACCESS_KEY,
                      aws_session_token=TOKEN)
    response = s3.list_objects(Bucket=bucket_name, Prefix=carpeta)
    max_num = 0
    for element in response.get('Contents', []):
        counter = int(element['Key'].split('-')[3].replace('.pdf',''))
        if(max_num<counter): max_num = counter
    return max_num+1

def eliminar_archivos_pdf_en_carpeta(carpeta):
    for archivo in os.listdir(carpeta):
        if archivo.endswith(".pdf"):
            ruta_completa = os.path.join(carpeta, archivo)
            try:
                os.remove(ruta_completa)
                print(f"Archivo eliminado: {archivo}")
            except Exception as e:
                print(f"No se pudo eliminar {archivo}: {e}")


def getEvent(name):
    for ev in events:
        if ev['nombre'] == name:
            return ev
        else : return False





def listen_to_sqs():
    try:
        # Recibe el mensaje de SQS
        message = sqs.receive_message(QueueUrl=queue_url_request, AttributeNames=['All'], MaxNumberOfMessages=1, WaitTimeSeconds=20)

        if 'Messages' in message:
            # Procesa el mensaje
            message_body = message['Messages'][0]['Body']
            
            # Elimina el mensaje de la cola
            receipt_handle = message['Messages'][0]['ReceiptHandle']
            sqs.delete_message(QueueUrl=queue_url_request, ReceiptHandle=receipt_handle)

            # hemos recibido un mensaje
            request = json.loads(message['Messages'][0]['Body'])
            print(request)

            name = request['name'].replace(' ','_')
            number = request['number']
            uid = request['uuid']

            print(name)
            print(number)


            if getEvent(name):
                #contamos cuantos hay disponibles
                numVendidas = contar_entradas(name)
                print(numVendidas)
                event = getEvent(name)
                if numVendidas+number<= event['entradas']:
                    output_filename = uid+'-'+name+'-'+str(numVendidas)+'-'+str(numVendidas+number-1)+".pdf"
                    CreaPDF.creaPDF(output_filename,name,event['fecha'],event['lugar'],event['hora'],event['duracion'],event['precio'],number)
                    subir_pdf(output_filename,bucket_name,name+'/'+output_filename)
                    eliminar_archivos_pdf_en_carpeta('./')
                    #respondemos al usuario
                    archivo = name+'/'+output_filename
                    message_body = f'{{"message": "Correct_Transaction","uuid":"{uid}","archivo":"{archivo}"}}'
                    sqs.send_message(QueueUrl=queue_url_response, MessageBody=message_body)

                else:
                    
                    message_body = f'{{"message": "Sold_Out","uuid":"{uid}"}}'
                    sqs.send_message(QueueUrl=queue_url_response, MessageBody=message_body)
                    print('No quedan entradas disponibles')
            else:
                message_body = f'{{"message": "No_Exists_Event","uuid":"{uid}"}}'
                sqs.send_message(QueueUrl=queue_url_response, MessageBody=message_body)
                print('No existe ese evento')


        else:
            print('Cola Vacía')
    except Exception as e:
        message_body = f'{{"message": "Fatal_Error"}}'
        sqs.send_message(QueueUrl=queue_url_response, MessageBody=message_body)


def main():
     while True:
          listen_to_sqs()

main()

