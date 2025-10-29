# Corporate Chat Application - AWS ECS Deployment Guide

This guide provides detailed instructions for deploying the Corporate Chat application to AWS ECS Fargate with public IP addresses.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [AWS Infrastructure Setup](#aws-infrastructure-setup)
4. [Docker Image Preparation](#docker-image-preparation)
5. [ECS Deployment](#ecs-deployment)
6. [Updating the Application](#updating-the-application)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- AWS CLI installed and configured
- Docker installed
- Git (for version control)
- AWS Account with appropriate permissions

### Required AWS Credentials
You need AWS credentials with permissions for:
- ECR (Elastic Container Registry)
- ECS (Elastic Container Service)
- VPC and networking
- IAM roles
- CloudWatch Logs
- Lambda (for Claude API invocation)
- S3 (for document storage)

### Environment Variables
Set these environment variables before starting:
```bash
export AWS_ACCESS_KEY_ID=<your-access-key-id>
export AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
export AWS_DEFAULT_REGION=ca-central-1
```

## Architecture Overview

### Components
- **Frontend**: React + Vite application served by Nginx
- **Backend**: FastAPI application with RAG capabilities
- **Database**: ChromaDB (vector database, embedded)
- **Document Storage**: AWS S3
- **LLM**: Claude API via AWS Lambda
- **Container Orchestration**: AWS ECS Fargate
- **Container Registry**: AWS ECR
- **Logging**: AWS CloudWatch

### Network Architecture
- VPC with public subnets
- Internet Gateway for public access
- Security Groups for port 80 access
- No load balancer (using public IPs directly)

## AWS Infrastructure Setup

### Step 1: Create VPC and Networking

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=corporatechat-vpc}]' \
  --region $AWS_DEFAULT_REGION \
  --query 'Vpc.VpcId' \
  --output text)

echo "VPC ID: $VPC_ID"

# Enable DNS hostnames
aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-hostnames \
  --region $AWS_DEFAULT_REGION

# Create Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=corporatechat-igw}]' \
  --region $AWS_DEFAULT_REGION \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

echo "Internet Gateway ID: $IGW_ID"

# Attach Internet Gateway to VPC
aws ec2 attach-internet-gateway \
  --vpc-id $VPC_ID \
  --internet-gateway-id $IGW_ID \
  --region $AWS_DEFAULT_REGION

# Create public subnets in two availability zones
SUBNET_1_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone ${AWS_DEFAULT_REGION}a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=corporatechat-subnet-1}]' \
  --region $AWS_DEFAULT_REGION \
  --query 'Subnet.SubnetId' \
  --output text)

SUBNET_2_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone ${AWS_DEFAULT_REGION}b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=corporatechat-subnet-2}]' \
  --region $AWS_DEFAULT_REGION \
  --query 'Subnet.SubnetId' \
  --output text)

echo "Subnet 1 ID: $SUBNET_1_ID"
echo "Subnet 2 ID: $SUBNET_2_ID"

# Create route table
ROUTE_TABLE_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=corporatechat-rt}]' \
  --region $AWS_DEFAULT_REGION \
  --query 'RouteTable.RouteTableId' \
  --output text)

echo "Route Table ID: $ROUTE_TABLE_ID"

# Create route to Internet Gateway
aws ec2 create-route \
  --route-table-id $ROUTE_TABLE_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID \
  --region $AWS_DEFAULT_REGION

# Associate subnets with route table
aws ec2 associate-route-table \
  --subnet-id $SUBNET_1_ID \
  --route-table-id $ROUTE_TABLE_ID \
  --region $AWS_DEFAULT_REGION

aws ec2 associate-route-table \
  --subnet-id $SUBNET_2_ID \
  --route-table-id $ROUTE_TABLE_ID \
  --region $AWS_DEFAULT_REGION
```

### Step 2: Create Security Groups

```bash
# Create security group for backend
BACKEND_SG_ID=$(aws ec2 create-security-group \
  --group-name corporatechat-backend-sg \
  --description "Security group for Corporate Chat backend" \
  --vpc-id $VPC_ID \
  --region $AWS_DEFAULT_REGION \
  --query 'GroupId' \
  --output text)

echo "Backend Security Group ID: $BACKEND_SG_ID"

# Allow port 80 (HTTP) for backend
aws ec2 authorize-security-group-ingress \
  --group-id $BACKEND_SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region $AWS_DEFAULT_REGION

# Create security group for frontend
FRONTEND_SG_ID=$(aws ec2 create-security-group \
  --group-name corporatechat-frontend-sg \
  --description "Security group for Corporate Chat frontend" \
  --vpc-id $VPC_ID \
  --region $AWS_DEFAULT_REGION \
  --query 'GroupId' \
  --output text)

echo "Frontend Security Group ID: $FRONTEND_SG_ID"

# Allow port 80 (HTTP) for frontend
aws ec2 authorize-security-group-ingress \
  --group-id $FRONTEND_SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region $AWS_DEFAULT_REGION
```

### Step 3: Create IAM Roles

```bash
# Create ECS task execution role trust policy
cat > /tmp/ecs-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create execution role
aws iam create-role \
  --role-name corporatechat-execution-role \
  --assume-role-policy-document file:///tmp/ecs-trust-policy.json \
  --region $AWS_DEFAULT_REGION

# Attach managed policy for ECS task execution
aws iam attach-role-policy \
  --role-name corporatechat-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
  --region $AWS_DEFAULT_REGION

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"
```

### Step 4: Create ECR Repositories

```bash
# Create backend ECR repository
aws ecr create-repository \
  --repository-name corporatechat-backend \
  --region $AWS_DEFAULT_REGION

# Create frontend ECR repository
aws ecr create-repository \
  --repository-name corporatechat-frontend \
  --region $AWS_DEFAULT_REGION
```

### Step 5: Create CloudWatch Log Groups

```bash
# Create log group for backend
aws logs create-log-group \
  --log-group-name /ecs/corporatechat-backend \
  --region $AWS_DEFAULT_REGION

# Create log group for frontend
aws logs create-log-group \
  --log-group-name /ecs/corporatechat-frontend \
  --region $AWS_DEFAULT_REGION
```

### Step 6: Create ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster \
  --cluster-name corporatechat-cluster \
  --region $AWS_DEFAULT_REGION
```

## Docker Image Preparation

### Step 1: Build Backend Image

**Important**: The backend requires AWS credentials to access Lambda and S3.

```bash
# Build backend image
sudo docker build -f Dockerfile.backend -t corporatechat-backend:latest .

# Login to ECR
aws ecr get-login-password --region $AWS_DEFAULT_REGION | \
  sudo docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com

# Tag image
sudo docker tag corporatechat-backend:latest \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-backend:latest

# Push to ECR
sudo docker push \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-backend:latest
```

### Step 2: Build Frontend Image

**Important**: Update the backend URL in Dockerfile.frontend before building.

```bash
# Edit Dockerfile.frontend to set the correct backend IP
# ARG VITE_API_BASE_URL=http://<BACKEND_IP>

# Build frontend image
sudo docker build -f Dockerfile.frontend -t corporatechat-frontend:latest .

# Tag image
sudo docker tag corporatechat-frontend:latest \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-frontend:latest

# Push to ECR
sudo docker push \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-frontend:latest
```

## ECS Deployment

### Step 1: Create Backend Task Definition

Create a file named `backend-task-def.json`:

```json
{
  "family": "corporatechat-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<AWS_ACCOUNT_ID>:role/corporatechat-execution-role",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<AWS_ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com/corporatechat-backend:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "AWS_ACCESS_KEY_ID",
          "value": "<YOUR_AWS_ACCESS_KEY_ID>"
        },
        {
          "name": "AWS_SECRET_ACCESS_KEY",
          "value": "<YOUR_AWS_SECRET_ACCESS_KEY>"
        },
        {
          "name": "AWS_DEFAULT_REGION",
          "value": "<YOUR_AWS_REGION>"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/corporatechat-backend",
          "awslogs-region": "<AWS_REGION>",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Security Note**: In production, use AWS Secrets Manager or ECS task roles instead of hardcoding credentials.

Register the task definition:
```bash
aws ecs register-task-definition \
  --cli-input-json file://backend-task-def.json \
  --region $AWS_DEFAULT_REGION
```

### Step 2: Create Backend ECS Service

```bash
aws ecs create-service \
  --cluster corporatechat-cluster \
  --service-name corporatechat-backend \
  --task-definition corporatechat-backend:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1_ID,$SUBNET_2_ID],securityGroups=[$BACKEND_SG_ID],assignPublicIp=ENABLED}" \
  --region $AWS_DEFAULT_REGION
```

### Step 3: Get Backend Public IP

Wait for the task to start (about 60-90 seconds), then get the public IP:

```bash
# Get backend task ARN
BACKEND_TASK_ARN=$(aws ecs list-tasks \
  --cluster corporatechat-cluster \
  --service-name corporatechat-backend \
  --region $AWS_DEFAULT_REGION \
  --query 'taskArns[0]' \
  --output text)

# Get network interface ID
BACKEND_ENI=$(aws ecs describe-tasks \
  --cluster corporatechat-cluster \
  --tasks "$BACKEND_TASK_ARN" \
  --region $AWS_DEFAULT_REGION \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
  --output text)

# Get public IP
BACKEND_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids "$BACKEND_ENI" \
  --region $AWS_DEFAULT_REGION \
  --query 'NetworkInterfaces[0].Association.PublicIp' \
  --output text)

echo "Backend IP: $BACKEND_IP"

# Test backend
curl http://$BACKEND_IP/health
```

### Step 4: Update Frontend with Backend IP

Update `Dockerfile.frontend` with the backend IP:
```dockerfile
ARG VITE_API_BASE_URL=http://<BACKEND_IP>
```

Then rebuild and push the frontend image (see Step 2 in Docker Image Preparation).

### Step 5: Create Frontend Task Definition

Create a file named `frontend-task-def.json`:

```json
{
  "family": "corporatechat-frontend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::<AWS_ACCOUNT_ID>:role/corporatechat-execution-role",
  "containerDefinitions": [
    {
      "name": "frontend",
      "image": "<AWS_ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com/corporatechat-frontend:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/corporatechat-frontend",
          "awslogs-region": "<AWS_REGION>",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register the task definition:
```bash
aws ecs register-task-definition \
  --cli-input-json file://frontend-task-def.json \
  --region $AWS_DEFAULT_REGION
```

### Step 6: Create Frontend ECS Service

```bash
aws ecs create-service \
  --cluster corporatechat-cluster \
  --service-name corporatechat-frontend \
  --task-definition corporatechat-frontend:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1_ID,$SUBNET_2_ID],securityGroups=[$FRONTEND_SG_ID],assignPublicIp=ENABLED}" \
  --region $AWS_DEFAULT_REGION
```

### Step 7: Get Frontend Public IP

```bash
# Wait for task to start
sleep 60

# Get frontend task ARN
FRONTEND_TASK_ARN=$(aws ecs list-tasks \
  --cluster corporatechat-cluster \
  --service-name corporatechat-frontend \
  --region $AWS_DEFAULT_REGION \
  --query 'taskArns[0]' \
  --output text)

# Get network interface ID
FRONTEND_ENI=$(aws ecs describe-tasks \
  --cluster corporatechat-cluster \
  --tasks "$FRONTEND_TASK_ARN" \
  --region $AWS_DEFAULT_REGION \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
  --output text)

# Get public IP
FRONTEND_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids "$FRONTEND_ENI" \
  --region $AWS_DEFAULT_REGION \
  --query 'NetworkInterfaces[0].Association.PublicIp' \
  --output text)

echo "========================================="
echo "DEPLOYMENT COMPLETE!"
echo "========================================="
echo "Frontend URL: http://$FRONTEND_IP"
echo "Backend URL: http://$BACKEND_IP"
echo "========================================="
```

## Updating the Application

### Update Backend

```bash
# 1. Make code changes
# 2. Rebuild image
sudo docker build -f Dockerfile.backend -t corporatechat-backend:latest .

# 3. Push to ECR
aws ecr get-login-password --region $AWS_DEFAULT_REGION | \
  sudo docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com

sudo docker tag corporatechat-backend:latest \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-backend:latest

sudo docker push \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-backend:latest

# 4. Force new deployment
aws ecs update-service \
  --cluster corporatechat-cluster \
  --service corporatechat-backend \
  --force-new-deployment \
  --region $AWS_DEFAULT_REGION

# 5. Get new IP (may change)
sleep 60
BACKEND_TASK_ARN=$(aws ecs list-tasks \
  --cluster corporatechat-cluster \
  --service-name corporatechat-backend \
  --region $AWS_DEFAULT_REGION \
  --query 'taskArns[0]' \
  --output text)

BACKEND_ENI=$(aws ecs describe-tasks \
  --cluster corporatechat-cluster \
  --tasks "$BACKEND_TASK_ARN" \
  --region $AWS_DEFAULT_REGION \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
  --output text)

BACKEND_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids "$BACKEND_ENI" \
  --region $AWS_DEFAULT_REGION \
  --query 'NetworkInterfaces[0].Association.PublicIp' \
  --output text)

echo "New Backend IP: $BACKEND_IP"
```

**Note**: If backend IP changes, you must update and redeploy the frontend.

### Update Frontend

```bash
# 1. Update Dockerfile.frontend with current backend IP
# ARG VITE_API_BASE_URL=http://<BACKEND_IP>

# 2. Rebuild image
sudo docker build -f Dockerfile.frontend -t corporatechat-frontend:latest .

# 3. Push to ECR
aws ecr get-login-password --region $AWS_DEFAULT_REGION | \
  sudo docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com

sudo docker tag corporatechat-frontend:latest \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-frontend:latest

sudo docker push \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-frontend:latest

# 4. Force new deployment
aws ecs update-service \
  --cluster corporatechat-cluster \
  --service corporatechat-frontend \
  --force-new-deployment \
  --region $AWS_DEFAULT_REGION

# 5. Get new IP
sleep 60
FRONTEND_TASK_ARN=$(aws ecs list-tasks \
  --cluster corporatechat-cluster \
  --service-name corporatechat-frontend \
  --region $AWS_DEFAULT_REGION \
  --query 'taskArns[0]' \
  --output text)

FRONTEND_ENI=$(aws ecs describe-tasks \
  --cluster corporatechat-cluster \
  --tasks "$FRONTEND_TASK_ARN" \
  --region $AWS_DEFAULT_REGION \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
  --output text)

FRONTEND_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids "$FRONTEND_ENI" \
  --region $AWS_DEFAULT_REGION \
  --query 'NetworkInterfaces[0].Association.PublicIp' \
  --output text)

echo "New Frontend URL: http://$FRONTEND_IP"
```

## Troubleshooting

### Check Service Status

```bash
# Check service status
aws ecs describe-services \
  --cluster corporatechat-cluster \
  --services corporatechat-backend corporatechat-frontend \
  --region $AWS_DEFAULT_REGION
```

### Check Task Status

```bash
# List tasks
aws ecs list-tasks \
  --cluster corporatechat-cluster \
  --region $AWS_DEFAULT_REGION

# Describe specific task
aws ecs describe-tasks \
  --cluster corporatechat-cluster \
  --tasks <TASK_ARN> \
  --region $AWS_DEFAULT_REGION
```

### View Logs

```bash
# Backend logs
aws logs tail /ecs/corporatechat-backend \
  --region $AWS_DEFAULT_REGION \
  --follow

# Frontend logs
aws logs tail /ecs/corporatechat-frontend \
  --region $AWS_DEFAULT_REGION \
  --follow
```

### Common Issues

#### 1. CORS Errors
- **Symptom**: Frontend shows CORS policy errors
- **Solution**: Ensure backend CORS settings allow the frontend origin
- **Check**: `backend/main.py` has `allow_origins=["*"]` and `allow_credentials=False`

#### 2. Lambda Credentials Error
- **Symptom**: Backend logs show "Unable to locate credentials"
- **Solution**: Ensure AWS credentials are set in the backend task definition environment variables

#### 3. Task Won't Start
- **Symptom**: Task stays in PENDING status
- **Solution**: Check CloudWatch logs for error messages, verify security groups allow traffic

#### 4. Can't Access Application
- **Symptom**: HTTP timeout when accessing public IPs
- **Solution**:
  - Verify security groups allow port 80 from 0.0.0.0/0
  - Ensure subnets have route to Internet Gateway
  - Confirm tasks have public IPs assigned

#### 5. Backend IP Changes
- **Symptom**: Frontend can't connect after backend restart
- **Solution**: ECS Fargate tasks get new IPs on restart. You must:
  1. Get new backend IP
  2. Update Dockerfile.frontend
  3. Rebuild and redeploy frontend

### Health Check Commands

```bash
# Check backend health
curl http://<BACKEND_IP>/health

# Check frontend (should return HTML)
curl http://<FRONTEND_IP>

# Test backend chat endpoint
curl -X POST http://<BACKEND_IP>/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"text":"test","isUser":true}],"context":{}}'
```

## Production Recommendations

For production deployments, consider these improvements:

1. **Use Application Load Balancer**: Provides stable DNS names instead of changing IPs
2. **Use ECS Task Roles**: Instead of hardcoding credentials in task definitions
3. **Use AWS Secrets Manager**: For storing sensitive credentials
4. **Enable HTTPS**: Use ACM certificates with ALB
5. **Add Auto Scaling**: Configure ECS service auto-scaling based on CPU/memory
6. **Use Private Subnets**: Deploy tasks in private subnets with NAT Gateway
7. **Enable Container Insights**: For enhanced monitoring
8. **Set up CI/CD**: Use AWS CodePipeline or GitHub Actions for automated deployments
9. **Add Health Checks**: Configure ECS health checks for automatic recovery
10. **Enable Backup**: Regular snapshots of S3 documents and configurations

## Cost Optimization

- Use Fargate Spot for non-production workloads
- Right-size CPU and memory allocations
- Enable CloudWatch Logs retention policies
- Delete unused ECR images
- Stop services when not in use (development environments)

## Security Best Practices

1. Never commit AWS credentials to version control
2. Use IAM roles with least privilege
3. Enable VPC Flow Logs for network monitoring
4. Regularly update Docker base images
5. Scan images for vulnerabilities before deployment
6. Use AWS WAF if using ALB
7. Enable CloudTrail for audit logging
8. Implement network segmentation with security groups

## Support and Maintenance

### Monitoring
- Set up CloudWatch alarms for service health
- Monitor ECS metrics (CPU, memory, network)
- Track application logs for errors

### Regular Maintenance
- Update dependencies regularly
- Review and rotate credentials
- Update Docker base images
- Review and optimize costs monthly

## Cleanup

To delete all resources:

```bash
# Delete services
aws ecs update-service --cluster corporatechat-cluster --service corporatechat-backend --desired-count 0 --region $AWS_DEFAULT_REGION
aws ecs update-service --cluster corporatechat-cluster --service corporatechat-frontend --desired-count 0 --region $AWS_DEFAULT_REGION
aws ecs delete-service --cluster corporatechat-cluster --service corporatechat-backend --region $AWS_DEFAULT_REGION --force
aws ecs delete-service --cluster corporatechat-cluster --service corporatechat-frontend --region $AWS_DEFAULT_REGION --force

# Delete cluster
aws ecs delete-cluster --cluster corporatechat-cluster --region $AWS_DEFAULT_REGION

# Delete ECR repositories
aws ecr delete-repository --repository-name corporatechat-backend --force --region $AWS_DEFAULT_REGION
aws ecr delete-repository --repository-name corporatechat-frontend --force --region $AWS_DEFAULT_REGION

# Delete log groups
aws logs delete-log-group --log-group-name /ecs/corporatechat-backend --region $AWS_DEFAULT_REGION
aws logs delete-log-group --log-group-name /ecs/corporatechat-frontend --region $AWS_DEFAULT_REGION

# Delete security groups
aws ec2 delete-security-group --group-id $BACKEND_SG_ID --region $AWS_DEFAULT_REGION
aws ec2 delete-security-group --group-id $FRONTEND_SG_ID --region $AWS_DEFAULT_REGION

# Detach and delete Internet Gateway
aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID --region $AWS_DEFAULT_REGION
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID --region $AWS_DEFAULT_REGION

# Delete subnets
aws ec2 delete-subnet --subnet-id $SUBNET_1_ID --region $AWS_DEFAULT_REGION
aws ec2 delete-subnet --subnet-id $SUBNET_2_ID --region $AWS_DEFAULT_REGION

# Delete route table (disassociate first)
aws ec2 delete-route-table --route-table-id $ROUTE_TABLE_ID --region $AWS_DEFAULT_REGION

# Delete VPC
aws ec2 delete-vpc --vpc-id $VPC_ID --region $AWS_DEFAULT_REGION

# Delete IAM role
aws iam detach-role-policy --role-name corporatechat-execution-role --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam delete-role --role-name corporatechat-execution-role
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-29  
**Deployment Region**: ca-central-1 (Canada Central)
