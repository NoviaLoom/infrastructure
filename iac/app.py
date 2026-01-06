#!/usr/bin/env python3
import os
import aws_cdk as cdk
from novialoom_infra.stacks.network_stack import NetworkStack
from novialoom_infra.stacks.compute_stack import ComputeStack

app = cdk.App()

# Environnement par défaut (Paris eu-west-3)
env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'), 
    region='eu-west-3'
)

# 1. Stack Réseau
network_stack = NetworkStack(app, "NovialoomNetworkStack", env=env)

# 2. Stack Compute (Lambdas & API Gateway)
# On passe le VPC de la stack réseau à la stack compute
compute_stack = ComputeStack(
    app, "NovialoomComputeStack", 
    vpc=network_stack.vpc,
    env=env
)

app.synth()
