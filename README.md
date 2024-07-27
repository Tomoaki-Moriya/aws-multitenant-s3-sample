# aws-multitenant-s3-sample

## Get Started

### Create User

```sh
$ aws cognito-idp admin-create-user \
--user-pool-id "region_xxxxx" \
--username "xxx@mail.com" \
--user-attributes \
Name=email,Value="xxx@mail.com" \
Name=email_verified,Value=true \
Name=custom:tenant_id,Value=tenant-1 \
--message-action SUPPRESS
```

```sh
$ aws cognito-idp admin-set-user-password \
--user-pool-id "region_xxxxx" \
--username "xxxxx-xxxx-xxxx-xxxx-xxxxx" \
--password 'XXX' \
--permanent
```
