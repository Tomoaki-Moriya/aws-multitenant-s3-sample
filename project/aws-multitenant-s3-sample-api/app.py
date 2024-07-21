import os
import boto3
from botocore.exceptions import ClientError
from chalice import (
    Chalice,
    CognitoUserPoolAuthorizer,
    Response,
    UnauthorizedError,
    BadRequestError,
)

USER_POOL_ID = os.environ["USER_POOL_ID"]
USER_POOL_CLIENT_ID = os.environ["USER_POOL_CLIENT_ID"]
IDENTITY_POOL_ID = os.environ["IDENTITY_POOL_ID"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
AWS_ACCOUNT_ID = os.environ["AWS_ACCOUNT_ID"]
REGION = "ap-northeast-1"

app = Chalice(app_name="aws-multitenant-s3-sample-api")
authorizer = CognitoUserPoolAuthorizer(
    name="AwsMultitenantS3SampleAuthorizer",
    provider_arns=[
        f"arn:aws:cognito-idp:{REGION}:{AWS_ACCOUNT_ID}:userpool/{USER_POOL_ID}"
    ],
)
cognito_client = boto3.client("cognito-idp")


def get_temporary_credentials(id_token: str):
    identity_response = cognito_client.get_id(
        IdentityPoolId=IDENTITY_POOL_ID,
        Logins={f"cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}": id_token},
    )
    identity_id = identity_response["IdentityId"]

    credentials_response = cognito_client.get_credentials_for_identity(
        IdentityId=identity_id,
        Logins={f"cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}": id_token},
    )
    credentials = credentials_response["Credentials"]
    return credentials


@app.route("/files/{key+}", methods=["GET"], authorizer=authorizer)
def index(key: str):
    bearer_token = (
        app.current_request.headers.get("Authorization")
        if app.current_request
        else None
    )
    id_token = bearer_token.replace("Bearer ", "") if bearer_token else None

    if not id_token:
        raise UnauthorizedError()

    credentials = get_temporary_credentials(id_token)
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretKey"],
        aws_session_token=credentials["SessionToken"],
    )

    try:
        obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
        return Response(
            body=obj["Body"].read(),
            status_code=200,
            headers={"Content-Type": obj["ContentType"]},
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return Response(
                body="Not Found",
                status_code=404,
            )
        else:
            return Response(
                body="Internal Server Error",
                status_code=500,
            )


@app.route("/login", methods=["POST"])
def login():
    request = app.current_request
    if request is None:
        raise BadRequestError()

    body = request.json_body
    if body is None:
        raise BadRequestError()

    username = body.get("username")
    password = body.get("password")
    if username is None or password is None:
        raise BadRequestError()

    try:
        response = cognito_client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
            ClientId=USER_POOL_CLIENT_ID,
        )
        return Response(
            body=response["AuthenticationResult"]["IdToken"], status_code=200
        )
    except ClientError:
        raise UnauthorizedError()
