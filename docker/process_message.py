#!/usr/bin/env python

"""
A Python Script located on an AWS ECS container.

1. ECS Service grabs SQS message containing file metadata from SQS Queue
2. ECS Service uses file metadata to download the JSON lines file from S3 Input
   Bucket
3. ECS Service goes line by line through the JSON file and performs calculation
   on the json object
5. ECS Service compiles results in new JSON File and outputs resulting file to
   S3 Output bucket
"""

import os
import json
import io
import time
import boto3


# Environment / Global Variables
INPUT_BUCKET_NAME = os.environ['s3InputBucket']
OUTPUT_BUCKET_NAME = os.environ['s3OutputBucket']
SQS_QUEUE_NAME = os.environ['SQSBatchQueue']
AWS_REGION = os.environ['AWSRegion']
OUTPUT_DIR = 'output/'

# AWS Clients / Resources
S3_CLIENT = boto3.client('s3', region_name=AWS_REGION)
S3_RESOURCE = boto3.resource('s3', region_name=AWS_REGION)
SQS_RESOURCE = boto3.resource('sqs', region_name=AWS_REGION)

def calculation(json_obj):
    """
    PERFORM YOUR CUSTOM CODE / CALCULATION ON THE JSON OBJECT HERE

    returns json object
    """

    new_obj = json_obj # PLACEHOLDER

    return new_obj


def create_dirs():
    """
    Create a directory for the S3 ouput file.
    """
    print("Creating directories...")
    for dirs in [OUTPUT_DIR]:
        if not os.path.exists(dirs):
            os.makedirs(dirs)


def process_message():
    """
    Process the sqs message
    No real error handling in this sample code. In case of error we'll put
    the message back in the queue and make it visable again. It will end up in
    the dead letter queue after five failed attempts.
    """
    for message in get_messages_from_sqs():
        try:
            print("Getting messages from SQS...")
            print(str(message))
            message_content = json.loads(message.body)
            file = message_content['Records'][0]['s3']['object']['key']
            local_file = os.path.basename(file)

            print("processing file...")
            process_file(file, local_file)

            print("uploading results...")
            s3_upload_file(local_file)

            print("cleaning up files...")
            cleanup_files(local_file)

        except Exception as err:
            print("error occurred: " + str(err))
            message.change_visibility(VisibilityTimeout=0)
            continue
        else:
            print("deleting sqs message...")
            message.delete()


def cleanup_files(file):
    """
    Delete the temporarily downloaded local file.
    """
    os.remove(OUTPUT_DIR + file)

def s3_upload_file(file):
    """
    Upload a local file to S3.
    """
    S3_CLIENT.upload_file(OUTPUT_DIR + file,
                          OUTPUT_BUCKET_NAME, OUTPUT_DIR + file)


def get_messages_from_sqs():
    """
    Poll the SQS Queue for new messages.
    """
    results = []
    queue = SQS_RESOURCE.get_queue_by_name(QueueName=SQS_QUEUE_NAME)
    for message in queue.receive_messages(VisibilityTimeout=120,
                                          WaitTimeSeconds=20,
                                          MaxNumberOfMessages=10):
        results.append(message)
    return results


def process_file(file, local_file):
    """
    Process an S3 JSON file.

    1. Get the S3 Object
    2. load into JSON line-by-line
    3. For each line, call an API to perform a calculation on a specific column.
    4. Output results to a local file.
    """
    start_time = time.time()
    content_object = S3_RESOURCE.Object(INPUT_BUCKET_NAME, file)
    file_buffer = io.StringIO()
    file_buffer = content_object.get()['Body'].read().decode('utf-8')

    json_lines = []
    for line in file_buffer.splitlines():
        json_obj = json.loads(line)

        new_obj = calculation(json_obj)

        json_lines.append(new_obj)

    print("writing json to file...")
    file_path = OUTPUT_DIR + local_file
    print(file_path)
    with open(file_path, 'w') as outfile:
        json.dump(json_lines, outfile)

    print("--- %s seconds ---", (time.time() - start_time))

def main():
    """
    Begin the process message process. continously poll for any new SQS messages.
    """
    create_dirs()
    while True:
        process_message()


if __name__ == "__main__":
    main()
