
# Welcome to your CDK Python project!

## Getting Started

This is a blank project for Python development with CDK.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the .env
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .env
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .env/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .env\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

Since we are going to focus on writing tests, install the dev dependencies.

```
$ pip install -r requirements-dev.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.


## Adding Unit tests for the Lambdas

* Create a file named `pytest.ini` with the contents:
    ```ini
    [pytest]
    testpaths = 
        tests/**/*_test.py
        
    pythonpath = 
        .
    ```

* Given our lambdas reside in a directory named `lambda` we will have an issue importing them for use in our tests.  This is because `lambda` is a python language keyword.  Rename this directory to `lambdas`: (e.g. bash): `mv lambda lambdas`

* Modify `cdk_workshop/hitcounter.py` to specify the updated code location `lambdas` in the handler's `code` attribute:
    ```python
    self._handler = _lambda.Function(
        self,
        "HitCounterHandler",
        runtime=_lambda.Runtime.PYTHON_3_7,
        handler="hitcount.handler",
        code=_lambda.Code.from_asset("lambdas"),
        environment={
            "DOWNSTREAM_FUNCTION_NAME": downstream.function_name,
            "HITS_TABLE_NAME": self._table.table_name,
        },
    )
    ```

* Do the same in `cdk_workshop/cdk_workshop_stack.py` for the HelloWorld handler:
    ```python
    my_lambda = _lambda.Function(
        self,
        "HelloHandler",
        runtime=_lambda.Runtime.PYTHON_3_7,
        code=_lambda.Code.from_asset("lambdas"),
        handler="hello.handler",
    )
    ```

* Create the directory `tests/unit` and add a file named `hello_test.py` with the contents:
    ```python
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
    ```
    Please note the test will not run unless your method begins with `test_`

* Execute the tests: `pytest`

* Ensure your test is passing:
    ```bash
    $ pytest
    ======================================================== test session starts ========================================================
    platform darwin -- Python 3.10.10, pytest-7.2.1, pluggy-1.0.0
    rootdir: /Users/kttinn/src/aws-cdk-intro-workshop/code/python/unit-test-cicd-workshop, configfile: pytest.ini, testpaths: tests/**/*_test.py
    plugins: typeguard-2.13.3
    collected 1 item                                                                                                                    

    tests/unit/hello_test.py .                                                                                                    [100%]

    ========================================================= 1 passed in 0.01s =========================================================
    ```

* In the `tests/unit` directory, add a file named `hitcount_test.py` with the contents: 
    ```python
    import os, json
    from unittest import TestCase
    from unittest.mock import patch

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
    ```

* Run the tests again and see two pass.  Notice the usage of `patch` to mock boto3 calls to AWS APIs.  We'll dive deeper into mocking shortly.

* Add another test to `hitcount_test.py` to ensure DynamoDB is called:
    ```python
    def test_handler_calls_dynamo(self, boto_mock):
        boto_mock.return_value = self.downstreamLambdaResponse
            
        handler(self.event, {})
        
        boto_mock.assert_any_call('UpdateItem', {
            'TableName': 'hitsTableName1',
            'Key': {'path': self.event['path']},
            'UpdateExpression': 'ADD hits :incr',
            'ExpressionAttributeValues': {':incr': 1}
        })
    ```

* And finally a test to ensure the downstream lambda is called correctly:
    ```python
    def test_handler_calls_downstream_lambda(self, boto_mock):
        boto_mock.return_value = self.downstreamLambdaResponse
            
        handler(self.event, {})
        
        boto_mock.assert_any_call('Invoke', {
            'FunctionName': 'downstreamFunctionName1',
            'Payload': '{"path": "' + self.event['path'] + '"}'
        })
    ```



## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation
