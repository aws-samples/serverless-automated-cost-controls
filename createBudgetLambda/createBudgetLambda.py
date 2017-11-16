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
import os
import datetime
import requests
import calendar
from botocore.exceptions import ClientError

# lambda function that interacts creates a budget in response to
# Input parameters: None
# Environment Variable:  AccountId - gets set from cfn
# This function creates (and deletes) a budget for Project Beta
def lambda_handler(context,event):
    try:
        budgetClient = boto3.client('budgets')
        sns = boto3.resource('sns')

        responseStatus = 'SUCCESS'
        responseData = {}


        print "first list the existing budgets"
        response = budgetClient.describe_budgets(AccountId= os.environ['AccountId'], MaxResults= 99)
        print response

        if context['RequestType'] == 'Delete':
 	    # Delete the Budget
            print "deleting the budget"
            response = budgetClient.delete_budget(AccountId= os.environ['AccountId'],BudgetName= 'Monthly EC2 Budget for Beta')
            print response
            responseData = {'Success': 'Budget Deleted.'}
            sendResponse(event, context, responseStatus, responseData)

        if context['RequestType'] == 'Create':
            response = budgetClient.create_budget(
                AccountId= os.environ['AccountId'],
                Budget={
                    'BudgetName': 'Monthly EC2 Budget for Beta',
                    'BudgetLimit': {
                        'Amount': '2',
                        'Unit': 'USD'
                    },
                    'CostFilters': {
                        'Service': [
                            'Amazon Elastic Compute Cloud - Compute',
                        ],
                        'TagKeyValue': ['user:Project$Beta']
                    },
                    'CostTypes': {
                        'IncludeTax': True,
                        'IncludeSubscription': True,
                        'UseBlended': False
                    },
                    'TimeUnit': 'MONTHLY',
                    'TimePeriod': {
                        'Start': datetime.datetime(datetime.date.today().year, datetime.date.today().month, calendar.monthrange(datetime.date.today().year,datetime.date.today().month)[0]),
                        'End': datetime.datetime(datetime.date.today().year, datetime.date.today().month, calendar.monthrange(datetime.date.today().year,datetime.date.today().month)[1])
                    },
                    'CalculatedSpend': {
                        'ActualSpend': {
                            'Amount': '1.75',
                            'Unit': 'USD'
                        },
                        'ForecastedSpend': {
                            'Amount': '1.75',
                            'Unit': 'USD'
                        }
                    },
                    'BudgetType': 'COST'
                },
                NotificationsWithSubscribers=[
                {
                    'Notification': {
                        'NotificationType': 'ACTUAL',
                        'ComparisonOperator': 'GREATER_THAN',
                        'Threshold': 1.75
                    },
                    'Subscribers': [
                    {
                        'SubscriptionType': 'SNS',
                        'Address': os.environ['BudgetNotificationArn']
                    },
                    ]
                }
                ]
            )

            print response
            responseData = {'Success': 'Budget Created.'}

            sendResponse(event, context, responseStatus, responseData)

    except ClientError as e:
        responseStatus = 'FAILED'
        responseData = {'Failed': 'Failed to create Budget.'}
        if e.response['Error']['Code'] == 'DuplicateRecordException':
            print "Just hit a Duplicate Record Exception. Need to talk to the Budgets team about this. Wil proceed, since it does not seem to make any functional diff"
            responseStatus = 'SUCCESS'
            responseData = {'Success': 'Success depite the duplicate record error!'}
            sendResponse(event, context, responseStatus, responseData)
        elif e.response['Error']['Code'] == 'NoSuchEntity':
            print "Incorrect Policy Arn. Either the policy is not attached to the given group, or the policy arn does not exist"
            sendResponse(event, context, responseStatus, responseData)
        else:
            print "Unexpected error: %s" % e
            sendResponse(event, context, responseStatus, responseData)


def sendResponse(event, context, responseStatus, responseData):
    responseBody = {'Status': responseStatus,
                    'Reason': 'See the details in CloudWatch Log Stream ',
                    'PhysicalResourceId': context['ServiceToken'],
                    'StackId': context['StackId'],
                    'RequestId': context['RequestId'],
                    'LogicalResourceId': context['LogicalResourceId'],
                    'Data': responseData}
    print 'RESPONSE BODY:n' + json.dumps(responseBody)
    try:
        req = requests.put(context['ResponseURL'], data=json.dumps(responseBody))
        if req.status_code != 200:
            print req.text
            raise Exception('Recieved non 200 response while sending response to CFN.')
        return
    except requests.exceptions.RequestException as e:
        print e
        raise

if __name__ == '__main__':
    lambda_handler('event', 'handler')
