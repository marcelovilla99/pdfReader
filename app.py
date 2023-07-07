import json
from pdfReader import getResponse

GET_PDF_PATH = "/getPDF"
GET_VALIDATION_PATH = "/getValidation"


def handler(event, context):
    print("handler function executing...")
    path = event['rawPath']
    print('printing THE THE THE path.................')
    print(path)

    if path == GET_VALIDATION_PATH:
        return {
            'statusCode': 200,
            'body': json.dumps('Lambda function up and running.')
        }

    if path == GET_PDF_PATH:
        request = json.loads(event['body'])
        try:
            response = getResponse(request)
            return {
                'statusCode': 200,
                'body': json.dumps(response)
            }
        except Exception as e:
            print(e)
            return {
                'statusCode': 400,
                'body': 'An error occurred while running the algorithm.',
            }

    # TODO implement
    return {
        'statusCode': 400,
        'body': json.dumps('Path not recognized. Please verify.')
    }
