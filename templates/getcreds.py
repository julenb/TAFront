import boto3

# Especifica el nombre del perfil de AWS que deseas utilizar
aws_profile_name = 'nombre_de_tu_perfil_aws'

# Crea un cliente STS utilizando el perfil de AWS
session = boto3.Session(profile_name=aws_profile_name)
sts_client = session.client('sts')

# Obtiene las credenciales temporales
response = sts_client.get_session_token()

# Imprime las credenciales
credentials = response['Credentials']
print(f"Access Key ID: {credentials['AccessKeyId']}")
print(f"Secret Access Key: {credentials['SecretAccessKey']}")
print(f"Session Token: {credentials['SessionToken']}")
print(f"Expiration: {credentials['Expiration']}")

