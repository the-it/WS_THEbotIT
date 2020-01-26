from aws_cdk import aws_s3
from aws_cdk import core


class InfrastructureStack(core.Stack):
    def __init__(self, scope: core.Construct, identifier: str, **kwargs) -> None:
        super().__init__(scope, identifier, **kwargs)
        core.CfnOutput(self,id="tada", value=self.environment)
        print(self.account)
        for i in range(1):
            aws_s3.Bucket(self, f"awesomeesommerbucket{i}", bucket_name=f"awesomeesommerbucket{i}{self.env}duh", removal_policy=core.RemovalPolicy.DESTROY)

    @property
    def env(self):
        if self.account == "491171445909":
            return "prd"
        return "tst"


