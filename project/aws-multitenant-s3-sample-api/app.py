import os

import boto3
from botocore.exceptions import ClientError
from chalice import (
    BadRequestError,
    Chalice,
    CognitoUserPoolAuthorizer,
    CORSConfig,
    NotFoundError,
    Response,
    UnauthorizedError,
)

USER_POOL_ID = os.environ["USER_POOL_ID"]
USER_POOL_CLIENT_ID = os.environ["USER_POOL_CLIENT_ID"]
IDENTITY_POOL_ID = os.environ["IDENTITY_POOL_ID"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
AWS_ACCOUNT_ID = os.environ["AWS_ACCOUNT_ID"]
REGION = "ap-northeast-1"

app = Chalice(app_name="aws-multitenant-s3-sample-api")
app.api.binary_types = ["*/*"]
cors_config = CORSConfig(
    allow_origin="*",  # Danger. Only for testing.
    allow_headers=[],
    max_age=600,
    expose_headers=[],
    allow_credentials=True,
)


authorizer = CognitoUserPoolAuthorizer(
    name="AwsMultitenantS3SampleAuthorizer",
    provider_arns=[
        f"arn:aws:cognito-idp:{REGION}:{AWS_ACCOUNT_ID}:userpool/{USER_POOL_ID}"
    ],
)

cognito_idp_client = boto3.client("cognito-idp")
cognito_id_client = boto3.client("cognito-identity")


def get_temporary_credentials(id_token: str):
    identity_response = cognito_id_client.get_id(
        IdentityPoolId=IDENTITY_POOL_ID,
        Logins={f"cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}": id_token},
    )
    identity_id = identity_response["IdentityId"]

    credentials_response = cognito_id_client.get_credentials_for_identity(
        IdentityId=identity_id,
        Logins={f"cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}": id_token},
    )
    credentials = credentials_response["Credentials"]
    return credentials


@app.route("/files/{key+}", methods=["GET"], authorizer=authorizer, cors=cors_config)
def index():
    key = (
        app.current_request.uri_params.get("key")
        if app.current_request and app.current_request.uri_params
        else None
    )
    if key is None:
        raise NotFoundError()

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
    except ClientError:
        raise NotFoundError()


@app.route("/login", methods=["POST"], cors=cors_config)
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
        response = cognito_idp_client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
            ClientId=USER_POOL_CLIENT_ID,
        )
        return Response(
            body=response["AuthenticationResult"]["IdToken"], status_code=200
        )
    except ClientError:
        raise UnauthorizedError()
