"""
**********************************************************************************************************************
 *  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved                                            *
 *                                                                                                                    *
 *  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated      *
 *  documentation files (the "Software"), to deal in the Software without restriction, including without limitation   *
 *  the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and  *
 *  to permit persons to whom the Software is furnished to do so.                                                     *
 *                                                                                                                    *
 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO  *
 *  THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE    *
 *  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF         *
 *  CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS *
 *  IN THE SOFTWARE.                                                                                                  *
 **********************************************************************************************************************
"""

import json
import boto3
import os

def lambda_handler(event, context):
    # Uncomment print line for debugging
    # print(event)

    # Establish an empty response and loop counter
    loop_counter = 0

    # Process the incoming S3 event
    for recording in event['Records']:

        # Increment loop
        loop_counter = loop_counter+1

        # Grab incoming data elements from the S3 event
        try:
            recording_key = recording['s3']['object']['key']
            recording_name = recording_key.replace('voicemail_recordings/','')
            contact_id = recording_name.replace('.wav','')
            recording_bucket = recording['s3']['bucket']['name']

        except:
            print('Record ' + str(loop_counter) + ' Result: Failed to extract data from event')
            continue

        # Establish the S3 client and get the object tags
        try:
            s3_client = boto3.client('s3')
            object_data = s3_client.get_object_tagging(
                Bucket=recording_bucket,
                Key=recording_key
            )

            object_tags = object_data['TagSet']
            loaded_tags = {}

            for i in object_tags:
                loaded_tags.update({i['Key']:i['Value']})

        except:
            print('Record ' + str(loop_counter) + ' Result: Failed to extract tags from object')
            continue

        # Build the Recording URL
        try:
            recording_url = 'https://'+recording_bucket+'.s3-'+recording['awsRegion']+'.amazonaws.com/'+recording_key

        except:
            print('Record ' + str(loop_counter) + ' Result: Failed to generate recording URL')
            continue

        # Do the transcription
        try:
            # Esteablish the client
            transcribe_client = boto3.client('transcribe')

            # Submit the transcription job
            transcribe_response = transcribe_client.start_transcription_job(
                TranscriptionJobName=contact_id,
                LanguageCode=loaded_tags['vm_lang'],
                MediaFormat='wav',
                Media={
                    'MediaFileUri': recording_url
                },
                OutputBucketName=os.environ['s3_transcripts_bucket']
            )

        except:
            print('Record ' + str(loop_counter) + ' Result: Transcription job failed')
            continue

        print('Record ' + str(loop_counter) + ' Result: Success!')

    return {
        'status': 'complete',
        'result': str(loop_counter) + ' records processed'
    }
