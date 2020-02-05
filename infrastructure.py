#!/usr/bin/env python3

from aws_cdk import core

from infrastructure.test_stack import InfrastructureStack

app = core.App()
InfrastructureStack(app, "infrastructure1")
InfrastructureStack(app, "infrastructure2")

app.synth()
