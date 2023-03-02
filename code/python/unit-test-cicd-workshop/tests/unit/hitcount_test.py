import os, json
from unittest import TestCase
from unittest.mock import patch, MagicMock

# Setup environment variables used by hitcount lambda, import fails otherwise
os.environ['DOWNSTREAM_FUNCTION_NAME'] = 'downstreamFunctionName1'
os.environ['HITS_TABLE_NAME'] = 'hitsTableName1'
from lambdas.hitcount import handler

@patch('botocore.client.BaseClient._make_api_call')
class TestHitCountLambda(TestCase):
    
    event = { 'path': 'path1' }
    downstreamLambdaResponsePayload = lambda: None
    downstreamLambdaResponsePayload.read = lambda: json.dumps({ 'value': 'value1' })
    downstreamLambdaResponse = { 'Payload': downstreamLambdaResponsePayload }

    def test_handler_returns_correct_response(self, boto_mock):
        boto_mock.return_value = self.downstreamLambdaResponse
            
        actual = handler(self.event, {})
        expected = json.loads(self.downstreamLambdaResponsePayload.read())
        self.assertEqual(expected, actual)

    def test_handler_calls_dynamo(self, boto_mock):
        boto_mock.return_value = self.downstreamLambdaResponse
            
        handler(self.event, {})
        
        boto_mock.assert_any_call('UpdateItem', {
            'TableName': 'hitsTableName1',
            'Key': {'path': self.event['path']},
            'UpdateExpression': 'ADD hits :incr',
            'ExpressionAttributeValues': {':incr': 1}
        })
    
    def test_handler_calls_downstream_lambda(self, boto_mock):
        boto_mock.return_value = self.downstreamLambdaResponse
            
        handler(self.event, {})
        
        boto_mock.assert_any_call('Invoke', {
            'FunctionName': 'downstreamFunctionName1',
            'Payload': '{"path": "' + self.event['path'] + '"}'
        })

    def test_handler_returns_400_if_no_path(self, boto_mock):
        boto_mock.return_value = self.downstreamLambdaResponse
        
        event_without_path = {}    
        expected = {
            'statusCode': 400,
            'body': json.dumps({ 'message': 'path not provided'})
        }
        actual = handler(event_without_path, {})
        
        self.assertEqual(expected, actual)

    @patch('time.time', MagicMock(return_value=12345))
    def test_handler_set_timestamp(self, boto_mock):
        boto_mock.return_value = self.downstreamLambdaResponse
            
        handler(self.event, {})
        
        boto_mock.assert_any_call('UpdateItem', {
            'TableName': 'hitsTableName1',
            'Key': {'path': self.event['path']},
            'UpdateExpression': 'SET timestamp :ts',
            'ExpressionAttributeValues': {':ts': 12345}
        })
