from aws_cdk import aws_s3
from aws_cdk import core


class InfrastructureStack(core.Stack):
    def __init__(self, scope: core.Construct, identifier: str, **kwargs) -> None:
        super().__init__(scope, identifier, **kwargs)
        core.CfnOutput(self, id="tada", value=self.account)
        aws_s3.Bucket(self, f"awesomeesommerbucket{identifier}", bucket_name=f"awesomeesommerbucket{identifier}duh", removal_policy=core.RemovalPolicy.DESTROY)
