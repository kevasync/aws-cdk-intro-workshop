from unittest import TestCase
from unittest.mock import patch
from lambdas.hello import * 


class TestHelloLambda(TestCase):
    def test_handler_returns_correct_response(self):
        event = { 'path': 'path1' }
        expected = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/plain'
            },
            'body': 'Hello, CDK! You have hit {}\n'.format(event['path'])
        }
        actual = handler(event, {})
        self.assertEqual(expected, actual)
