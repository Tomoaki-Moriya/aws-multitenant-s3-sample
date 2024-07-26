import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as cognito from "aws-cdk-lib/aws-cognito";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as iam from "aws-cdk-lib/aws-iam";

const PREFIX = "aws-multitenant-s3-sample";

export class SampleStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const userPool = new cognito.UserPool(this, `${PREFIX}-userpool-id`, {
      userPoolName: `${PREFIX}-userpool`,
      signInAliases: { email: true },
      standardAttributes: {
        email: {
          required: true,
          mutable: false,
        },
      },
      customAttributes: {
        tenant_id: new cognito.StringAttribute(),
      },
    });

    const identityPool = new cognito.CfnIdentityPool(
      this,
      `${PREFIX}-identity-pool-id`,
      {
        allowUnauthenticatedIdentities: false,
        cognitoIdentityProviders: [
          {
            clientId: userPool.userPoolId,
            providerName: userPool.userPoolProviderName,
          },
        ],
      }
    );

    new cognito.CfnIdentityPoolPrincipalTag(
      this,
      `${PREFIX}-identity-pool-tag-id`,
      {
        identityPoolId: identityPool.ref,
        identityProviderName: userPool.userPoolProviderName,
        principalTags: {
          tenant_id: "custom:tenant_id",
        },
      }
    );

    const bucket = new s3.Bucket(this, `${PREFIX}-bucket`, {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      bucketName: `${PREFIX}-bucket`,
    });

    const role = new iam.Role(this, `${PREFIX}-role`, {
      assumedBy: new iam.FederatedPrincipal(
        "cognito-identity.amazonaws.com",
        {
          StringEquals: {
            "cognito-identity.amazonaws.com:aud": userPool.userPoolId,
          },
          "ForAnyValue:StringLike": {
            "cognito-identity.amazonaws.com:amr": "authenticated",
          },
        },
        "sts:AssumeRoleWithWebIdentity"
      ).withSessionTags(),
    });
    role.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["s3:GetObject"],
        resources: [`${bucket.bucketArn}/\${aws:PrincipalTag/tenant_id}/*`],
      })
    );

    new cognito.CfnIdentityPoolRoleAttachment(
      this,
      `${PREFIX}-identity-pool-role-attachment-id`,
      {
        identityPoolId: identityPool.ref,
        roles: {
          authenticated: role.roleArn,
        },
      }
    );
  }
}
