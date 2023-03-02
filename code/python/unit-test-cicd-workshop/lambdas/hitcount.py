import json
import os
import time

import boto3

ddb = boto3.resource('dynamodb')
table = ddb.Table(os.environ['HITS_TABLE_NAME'])
_lambda = boto3.client('lambda')


def handler(event, context):
    print('request: {}'.format(json.dumps(event)))

    if not "path" in event:
        return {
            'statusCode': 400,
            'body': json.dumps({ 'message': 'path not provided'})
        }

    table.update_item(
        Key={'path': event['path']},
        UpdateExpression='ADD hits :incr',
        ExpressionAttributeValues={':incr': 1}
    )
    
    table.update_item(
        Key={'path': event['path']},
        UpdateExpression='SET timestamp :ts',
        ExpressionAttributeValues={':ts': time.time()}
    )

    resp = _lambda.invoke(
        FunctionName=os.environ['DOWNSTREAM_FUNCTION_NAME'],
        Payload=json.dumps(event),
    )

    body = resp['Payload'].read()

    print('downstream response: {}'.format(body))
    return json.loads(body)