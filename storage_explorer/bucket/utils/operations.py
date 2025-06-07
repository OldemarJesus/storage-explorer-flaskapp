from google.cloud import storage
from google.cloud.exceptions import NotFound
from storage_explorer import get_logger

logger = get_logger()

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'md'}

def create_bucket(bucket_name: str, api_key: dict) -> str:
    """Create a new GCP bucket."""
    client = storage.Client.from_service_account_info(api_key)
    bucket = client.bucket(bucket_name)
    bucket.create()
    return bucket

def list_files(bucket_name: str, api_key: dict) -> list:
    """List all files in a GCP bucket."""
    client = storage.Client.from_service_account_info(api_key)
    try:
        bucket = client.get_bucket(bucket_name)
    except NotFound:
        bucket = create_bucket(bucket_name, api_key)
    blobs = client.list_blobs(bucket)
    return [blob.name for blob in blobs]

def upload_file(bucket_name: str, filename: str, file, api_key: dict) -> None:
    client = storage.Client.from_service_account_info(api_key)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_file(file_obj=file)


# Utils
def allowed_file(filename):
    return '.' in filename and \
      filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS