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

import boto3
import json
from botocore.exceptions import ClientError

# lambda function that interacts with IAM
#   to replace the managed IAM policy on a given IAM Group.
# Input parameters:
#   GroupName = the IAM Group Name
#   DetachPolicyArn = the ARN of the policy that needs to be detached.
#   AttachPolicyArn = the ARN of the policy that needs to be attached.
#
# The function is triggered from a step function state machine
# The code attempts to first detach the given policy (referenced through its ARN)
# Then it attempts to attach the given policy (again, referenced through its ARN)

def lambda_handler(context,event):
    try:
        iam = boto3.resource('iam')
        print ("parameters: " + json.dumps(context))

        group           = iam.Group(context['GroupName'])
        group.detach_policy(PolicyArn=context['DetachPolicyArn'])
        group.attach_policy(PolicyArn=context['AttachPolicyArn'])

        return 200 #SUCCESS
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print ("Incorrect Policy Arn. Either the policy is not attached to the given group, or the policy arn does not exist")
            return e.response['ResponseMetadata']['HTTPStatusCode']
        else:
            print ("Unexpected error: %s" % e)
            return 500
