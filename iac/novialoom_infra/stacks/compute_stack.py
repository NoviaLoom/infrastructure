from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_ecr as ecr,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    Duration,
)
from constructs import Construct

class ComputeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        import aws_cdk as cdk
        from aws_cdk import aws_ecr_assets as ecr_assets
        cdk.Tags.of(self).add("Module", "Compute")
        cdk.Tags.of(self).add("Project", "Novialoom")

        # 0. Création d'un NOUVEAU Secret pour JWT (CDK Managed)
        self.jwt_secret = secretsmanager.Secret(
            self, "NovialoomJwtSecretFinal",
            secret_name="novialoom/infra/jwt-key",
            description="Secret pour l'authentification JWT inter-services Novialoom",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                password_length=32,
                exclude_punctuation=True
            )
        )

        # 1. Définition de l'API Gateway Centrale
        self.api = apigw.RestApi(
            self, "NovialoomCentralAPI",
            rest_api_name="Novialoom-Central-API",
            description="API Gateway centralisée pour les services B2B et B2C",
            deploy_options=apigw.StageOptions(stage_name="prod")
        )

        # 2. Helper pour créer des Lambdas Docker (via Assets locaux)
        def create_docker_lambda(service_name, memory=256, timeout=30):
            return _lambda.DockerImageFunction(
                self, f"Novialoom{service_name.replace('-', '').capitalize()}Lambda",
                function_name=f"novialoom-{service_name}-prod",
                description=f"Service {service_name} pour Novialoom (Production)",
                code=_lambda.DockerImageCode.from_image_asset(
                    directory="../", # Racine de /infrastructure
                    file="templates/Dockerfile.lambda",
                    build_args={"SERVICE_NAME": f"{service_name}-service"},
                    # Optimisation : utilise le cache Docker local
                    exclude=[
                        "iac/cdk.out",
                        "iac/.venv",
                        "iac/node_modules",
                        "**/__pycache__",
                        ".git"
                    ],
                    platform=ecr_assets.Platform.LINUX_ARM64
                ),
                architecture=_lambda.Architecture.ARM_64,
                memory_size=memory,
                timeout=Duration.seconds(timeout),
                vpc=vpc,
                vpc_subnets={"subnet_type": ec2.SubnetType.PRIVATE_WITH_EGRESS},
                environment={
                    "JWT_SECRET_NAME": self.jwt_secret.secret_name,
                    "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", ""),
                    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
                    "ENVIRONMENT": "production"
                }
            )

        # 3. Création des Lambdas de services (Uniquement si le dossier existe)
        import os

        def create_service_lambda(service_name, memory=256, timeout=30):
            # Le dossier attendu est services/{service_name}-service
            service_dir = f"{service_name}-service"
            full_path = os.path.join(os.path.dirname(__file__), "../../../services", service_dir)
            
            if not os.path.exists(full_path):
                print(f"⚠️ Skipping lambda {service_name}: directory {service_dir} not found")
                return None
                
            lambda_fn = create_docker_lambda(service_name, memory=memory, timeout=timeout)
            
            # Autoriser la Lambda à lire le secret JWT
            if lambda_fn:
                self.jwt_secret.grant_read(lambda_fn)
                
            return lambda_fn

        # Création des services existants
        core_lambda = create_service_lambda("core", memory=1024, timeout=60)
        
        # Permission pour Bedrock
        if core_lambda:
            core_lambda.add_to_role_policy(iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"] # En production, on peut restreindre aux ARNs des modèles spécifiques
            ))
        
        # Les gateways ne sont créées que si leurs dossiers existent
        b2b_lambda = create_service_lambda("gateway-b2b", memory=512)
        b2c_lambda = create_service_lambda("gateway-b2c", memory=512)

        # 4. Routing API Gateway
        if b2b_lambda:
            b2b_resource = self.api.root.add_resource("b2b")
            b2b_resource.add_proxy(default_integration=apigw.LambdaIntegration(b2b_lambda))

        if b2c_lambda:
            b2c_resource = self.api.root.add_resource("b2c")
            b2c_resource.add_proxy(default_integration=apigw.LambdaIntegration(b2c_lambda))

        if core_lambda:
            core_resource = self.api.root.add_resource("core")
            core_resource.add_proxy(default_integration=apigw.LambdaIntegration(core_lambda))

        # TODO: Créer les autres Lambdas de domaine (Analysis, Order, etc.)
        # self.analysis_lambda = create_docker_lambda("analysis", memory=1024, timeout=300)
