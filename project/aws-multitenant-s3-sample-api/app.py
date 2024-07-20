import os
from chalice import Chalice, CognitoUserPoolAuthorizer

COGNITO_USER_POOL_ARN = os.environ["COGNITO_USER_POOL_ARN"]

app = Chalice(app_name="aws-multitenant-s3-sample-api")
authorizer = CognitoUserPoolAuthorizer(
    "AwsMultitenantS3SampleAuthorizer",
    provider_arns=[COGNITO_USER_POOL_ARN],
)


@app.route("/", methods=["GET"], authorizer=authorizer)
def index():
    return {"hello": "world"}
