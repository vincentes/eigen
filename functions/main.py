from firebase_functions import storage_fn, options
from firebase_admin import initialize_app
from google.cloud import storage as gcs
import firebase_admin
# Cost analysis removed - use CLI for analysis
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    initialize_app()

@storage_fn.on_object_finalized(
    timeout_sec=540,  # 9 minutes timeout for o3
    memory=options.MemoryOption.GB_1,  # More memory might help
    max_instances=10
)
def on_file_upload(event):
    """
    Cloud Function triggered on file upload to Cloud Storage
    """
    # Get the storage event data
    data = event.data
    
    # Extract file information
    bucket_name = data.bucket
    file_name = data.name
    content_type = data.content_type or ''
    
    print(f"Archivo subido: {file_name} en bucket {bucket_name}")
    print(f"Tipo de contenido: {content_type}")

    if content_type.startswith('image/'):
        print(f"Imagen detectada: {file_name}")
        
        # Download and process the image directly
        try:
            # Get the storage client
            storage_client = gcs.Client()
            bucket_obj = storage_client.bucket(bucket_name)
            blob = bucket_obj.blob(file_name)
            
            # Download the image data
            image_data = blob.download_as_bytes()
            print(f"Imagen descargada: {len(image_data)} bytes")
            
            # Image processing completed - use CLI for detailed analysis
            print("Imagen procesada exitosamente")
            print("Para análisis detallado, use el CLI: python cli/main.py")
            
            return "OK"
            
        except Exception as e:
            print(f"Error descargando imagen: {e}")
            return "ERROR"
    else:
        print(f"El archivo no es una imagen: {file_name}")
        return "OK"