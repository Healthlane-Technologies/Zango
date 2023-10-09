import concurrent.futures
import boto3
from django.conf import settings 

def get_s3_client():
    s3 = boto3.client(
                    's3',
                    aws_access_key_id=settings.PACKAGE_BUCKET_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.PACKAGE_BUCKET_ACCESS_KEY_SECRET,
                    # region_name='your_region'
                    )
    return s3

def get_packages():
    bucket_name = settings.PACKAGE_BUCKET_NAME
    s3 = get_s3_client()
    paginator = s3.get_paginator('list_objects_v2')
    folders = {}
    
    for result in paginator.paginate(Bucket=bucket_name, Delimiter='/'):
        if result.get('CommonPrefixes') is not None:
            for prefix in result.get('CommonPrefixes'):
                folder_name = prefix.get('Prefix')
                subfolders = list_subfolders(bucket_name, folder_name)
                folders[folder_name[:-1]] = subfolders
                
    return folders

def list_subfolders(bucket_name, prefix):
    s3 = get_s3_client()
    paginator = s3.get_paginator('list_objects_v2')
    subfolders = []
    
    for result in paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/'):
        if result.get('CommonPrefixes') is not None:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_subfolder = {executor.submit(list_subfolders, bucket_name, sub_prefix.get('Prefix')): sub_prefix.get('Prefix') for sub_prefix in result.get('CommonPrefixes')}
                for future in concurrent.futures.as_completed(future_to_subfolder):
                    subfolder_name = future_to_subfolder[future]
                    subfolder_name_clean = subfolder_name[len(prefix):].strip('/')
                    if future.result():  # If there are sub-subfolders
                        subfolders.append({subfolder_name_clean: future.result()})
                    else:  # If there are no sub-subfolders
                        subfolders.append(subfolder_name_clean)
                
    return subfolders


