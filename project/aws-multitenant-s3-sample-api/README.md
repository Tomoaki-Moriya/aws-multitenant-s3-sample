# aws-multitenant-s3-sample-api

## Get Started

### Create Credentials

```sh
mkdir .chalice
```

```sh
echo '{
  "version": "2.0",
  "app_name": "aws-multitenant-s3-sample-api",
  "stages": {
    "prod": {
      "environment_variables": {
        "USER_POOL_ID": "xxxx",
        "USER_POOL_CLIENT_ID": "xxxx",
        "IDENTITY_POOL_ID": "xxxxxx",
        "BUCKET_NAME": "aws-multitenant-s3-sample-bucket",
        "AWS_ACCOUNT_ID": "xxxx"
      }
    }
  }
}
' > .chalice/config.json
```

## Deploy

```sh
AWS_PROFILE=xxx chalice deploy --stage prod
```
