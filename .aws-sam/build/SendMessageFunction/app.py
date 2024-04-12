import json
import boto3
import openai
import os

def lambda_handler(event, context):
    print("event",event)
    print("event.get('body', '{}') ==",event.get('body', '{}'))
    print("json.loads(event.get('body', '{}')) ==",json.loads(event.get('body', '{}')))
    try:
        # Get OpenAI API key from env
        openai.api_key = os.environ["OPENAI_API_KEY"]
    except KeyError:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "OpenAI API key is not provided.",
            }),
        }

    # Get input message and connectionId
    tesst = json.loads(event.get('body', '{}')).get('data')
    print("tesst",tesst)
    try:
        data = json.loads(event.get('body', '{}')).get('data')
        domain_name = event.get('requestContext', {}).get('domainName')
        stage = event.get('requestContext', {}).get('stage')
        connectionId = event.get('requestContext', {}).get('connectionId')
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": f"Invalid request format: {str(e)}",
            }),
        }

    apigw_management = boto3.client(
        'apigatewaymanagementapi', endpoint_url=F"https://{domain_name}/{stage}")

    # Request ChatGPT API
    print("data",data)
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                #{"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
                {"role": "user", "content": data},
            ],
            stream=True
        )
    except Exception  as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": f"OpenAI API error: {str(e)}",
            }),
        }

    # Send message to client
    for partial_message in response:
        print("partial_message", partial_message)
        choices = partial_message.choices
        if choices:
            choice = choices[0]
            delta = choice.delta
            if delta:
                content = delta.content
                if content:
                    apigw_management.post_to_connection(
                        ConnectionId=connectionId, Data=content)
    
    apigw_management.post_to_connection(
                        ConnectionId=connectionId, Data="END_OF_MESSAGES")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "data sent.",
        }),
    }
