from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_ecr as ecr,
    Duration,
)
from constructs import Construct

class ComputeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Définition de l'API Gateway Centrale
        self.api = apigw.RestApi(
            self, "NovialoomCentralAPI",
            rest_api_name="Novialoom-Central-API",
            description="API Gateway centralisée pour les services B2B et B2C",
            deploy_options=apigw.StageOptions(stage_name="prod")
        )

        # 2. Helper pour créer des Lambdas Docker
        def create_docker_lambda(service_name, memory=256, timeout=30):
            # Récupération du repo ECR (supposé existant ou géré par une stack de base)
            repo = ecr.Repository.from_repository_name(self, f"{service_name}Repo", f"novialoom-{service_name}")
            
            return _lambda.DockerImageFunction(
                self, f"Novialoom{service_name.capitalize()}Lambda",
                function_name=f"novialoom-{service_name}-prod",
                code=_lambda.DockerImageCode.from_ecr(repo),
                memory_size=memory,
                timeout=Duration.seconds(timeout),
                vpc=vpc,
                vpc_subnets=vpc.select_subnets(subnet_type=vpc.PRIVATE_WITH_EGRESS)
            )

        # 3. Création des Lambdas Gateways (Points d'entrée)
        b2b_lambda = create_docker_lambda("gateway-b2b", memory=512)
        b2c_lambda = create_docker_lambda("gateway-b2c", memory=512)

        # 4. Routing API Gateway
        b2b_resource = self.api.root.add_resource("b2b")
        b2b_resource.add_proxy(
            default_integration=apigw.LambdaIntegration(b2b_lambda)
        )

        b2c_resource = self.api.root.add_resource("b2c")
        b2c_resource.add_proxy(
            default_integration=apigw.LambdaIntegration(b2c_lambda)
        )

        # TODO: Créer les autres Lambdas de domaine (Analysis, Order, etc.)
        # self.analysis_lambda = create_docker_lambda("analysis", memory=1024, timeout=300)

