# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from __future__ import print_function

import json
import boto3
import os
from botocore.exceptions import ClientError

# lambda function that receives the Budget Notification and subsequently
#  triggers the action lambda (via step functions)
# Input parameters:
#  Notification from Budget
# Environment Variable: StateMachineArn
# Environment Variable: GroupName
# Environment Variable: DetachPolicyArn
# Environment Variable: AttachPolicyArn
# This function starts the execution of the
#  configured Step Function State Machine.

def lambda_handler(event, context):

    try:
        #budgetNotification = event['Records'][0]['Sns']['Message']
        #print("Notification from Budget (via SNS): " + budgetNotification)

        sfnClient = boto3.client('stepfunctions')

        inputs = {}
        inputs['AttachPolicyArn']=os.environ['AttachPolicyArn']
        inputs['DetachPolicyArn']=os.environ['DetachPolicyArn']
        inputs['GroupName'] = os.environ['GroupName']

        print (json.dumps(inputs))

        stateMachineArn = os.environ['StateMachineArn']
        response = sfnClient.start_execution(
            stateMachineArn=stateMachineArn,
            input=json.dumps(inputs)
        )

        print("Step Function Message ID: " + response['executionArn'])

        return 200
    except ClientError as e:
        print(e.response['Error']['Code'])
        if e.response['Error']['Code'] == 'NotFound':
            print("Incorrect Topic Arn. Could not find this topic")
            return e.response['ResponseMetadata']['HTTPStatusCode']
        else:
            print("Unexpected error: %s" % e)
            return 500
