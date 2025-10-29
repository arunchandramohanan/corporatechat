#!/bin/bash

#############################################
# Corporate Chat - AWS ECS Deployment Script
#############################################
# This script automates the complete deployment of the Corporate Chat application to AWS ECS Fargate
# Prerequisites:
# - AWS CLI installed and configured
# - Docker installed and running
# - AWS credentials set in environment variables

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "========================================="
    echo "$1"
    echo "========================================="
    echo ""
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    log_success "AWS CLI found"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    log_success "Docker found"
    
    # Check AWS credentials
    if [[ -z "$AWS_ACCESS_KEY_ID" ]] || [[ -z "$AWS_SECRET_ACCESS_KEY" ]]; then
        log_error "AWS credentials not set. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
        exit 1
    fi
    log_success "AWS credentials found"
    
    # Set default region if not set
    if [[ -z "$AWS_DEFAULT_REGION" ]]; then
        export AWS_DEFAULT_REGION="ca-central-1"
        log_warning "AWS_DEFAULT_REGION not set, using default: ca-central-1"
    fi
    log_success "AWS region: $AWS_DEFAULT_REGION"
    
    # Get AWS Account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    if [[ -z "$AWS_ACCOUNT_ID" ]]; then
        log_error "Failed to get AWS Account ID. Check your credentials."
        exit 1
    fi
    log_success "AWS Account ID: $AWS_ACCOUNT_ID"
}

# Create VPC and networking
create_vpc() {
    print_header "Step 1: Creating VPC and Networking"
    
    # Check if VPC already exists
    EXISTING_VPC=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=corporatechat-vpc" --query 'Vpcs[0].VpcId' --output text 2>/dev/null)
    if [[ "$EXISTING_VPC" != "None" ]] && [[ -n "$EXISTING_VPC" ]]; then
        log_warning "VPC already exists: $EXISTING_VPC"
        VPC_ID=$EXISTING_VPC
    else
        log_info "Creating VPC..."
        VPC_ID=$(aws ec2 create-vpc \
            --cidr-block 10.0.0.0/16 \
            --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=corporatechat-vpc}]' \
            --region $AWS_DEFAULT_REGION \
            --query 'Vpc.VpcId' \
            --output text)
        log_success "VPC created: $VPC_ID"
        
        # Enable DNS hostnames
        aws ec2 modify-vpc-attribute \
            --vpc-id $VPC_ID \
            --enable-dns-hostnames \
            --region $AWS_DEFAULT_REGION
        log_success "DNS hostnames enabled"
    fi
    
    # Create Internet Gateway
    EXISTING_IGW=$(aws ec2 describe-internet-gateways --filters "Name=tag:Name,Values=corporatechat-igw" --query 'InternetGateways[0].InternetGatewayId' --output text 2>/dev/null)
    if [[ "$EXISTING_IGW" != "None" ]] && [[ -n "$EXISTING_IGW" ]]; then
        log_warning "Internet Gateway already exists: $EXISTING_IGW"
        IGW_ID=$EXISTING_IGW
    else
        log_info "Creating Internet Gateway..."
        IGW_ID=$(aws ec2 create-internet-gateway \
            --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=corporatechat-igw}]' \
            --region $AWS_DEFAULT_REGION \
            --query 'InternetGateway.InternetGatewayId' \
            --output text)
        log_success "Internet Gateway created: $IGW_ID"
        
        # Attach to VPC
        aws ec2 attach-internet-gateway \
            --vpc-id $VPC_ID \
            --internet-gateway-id $IGW_ID \
            --region $AWS_DEFAULT_REGION 2>/dev/null || log_warning "IGW already attached"
        log_success "Internet Gateway attached to VPC"
    fi
    
    # Create subnets
    EXISTING_SUBNET_1=$(aws ec2 describe-subnets --filters "Name=tag:Name,Values=corporatechat-subnet-1" --query 'Subnets[0].SubnetId' --output text 2>/dev/null)
    if [[ "$EXISTING_SUBNET_1" != "None" ]] && [[ -n "$EXISTING_SUBNET_1" ]]; then
        log_warning "Subnet 1 already exists: $EXISTING_SUBNET_1"
        SUBNET_1_ID=$EXISTING_SUBNET_1
    else
        log_info "Creating subnet 1..."
        SUBNET_1_ID=$(aws ec2 create-subnet \
            --vpc-id $VPC_ID \
            --cidr-block 10.0.1.0/24 \
            --availability-zone ${AWS_DEFAULT_REGION}a \
            --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=corporatechat-subnet-1}]' \
            --region $AWS_DEFAULT_REGION \
            --query 'Subnet.SubnetId' \
            --output text)
        log_success "Subnet 1 created: $SUBNET_1_ID"
    fi
    
    EXISTING_SUBNET_2=$(aws ec2 describe-subnets --filters "Name=tag:Name,Values=corporatechat-subnet-2" --query 'Subnets[0].SubnetId' --output text 2>/dev/null)
    if [[ "$EXISTING_SUBNET_2" != "None" ]] && [[ -n "$EXISTING_SUBNET_2" ]]; then
        log_warning "Subnet 2 already exists: $EXISTING_SUBNET_2"
        SUBNET_2_ID=$EXISTING_SUBNET_2
    else
        log_info "Creating subnet 2..."
        SUBNET_2_ID=$(aws ec2 create-subnet \
            --vpc-id $VPC_ID \
            --cidr-block 10.0.2.0/24 \
            --availability-zone ${AWS_DEFAULT_REGION}b \
            --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=corporatechat-subnet-2}]' \
            --region $AWS_DEFAULT_REGION \
            --query 'Subnet.SubnetId' \
            --output text)
        log_success "Subnet 2 created: $SUBNET_2_ID"
    fi
    
    # Create route table
    EXISTING_RT=$(aws ec2 describe-route-tables --filters "Name=tag:Name,Values=corporatechat-rt" --query 'RouteTables[0].RouteTableId' --output text 2>/dev/null)
    if [[ "$EXISTING_RT" != "None" ]] && [[ -n "$EXISTING_RT" ]]; then
        log_warning "Route table already exists: $EXISTING_RT"
        ROUTE_TABLE_ID=$EXISTING_RT
    else
        log_info "Creating route table..."
        ROUTE_TABLE_ID=$(aws ec2 create-route-table \
            --vpc-id $VPC_ID \
            --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=corporatechat-rt}]' \
            --region $AWS_DEFAULT_REGION \
            --query 'RouteTable.RouteTableId' \
            --output text)
        log_success "Route table created: $ROUTE_TABLE_ID"
        
        # Create route to IGW
        aws ec2 create-route \
            --route-table-id $ROUTE_TABLE_ID \
            --destination-cidr-block 0.0.0.0/0 \
            --gateway-id $IGW_ID \
            --region $AWS_DEFAULT_REGION 2>/dev/null || log_warning "Route already exists"
        log_success "Route to Internet Gateway created"
        
        # Associate subnets
        aws ec2 associate-route-table \
            --subnet-id $SUBNET_1_ID \
            --route-table-id $ROUTE_TABLE_ID \
            --region $AWS_DEFAULT_REGION 2>/dev/null || log_warning "Subnet 1 already associated"
        
        aws ec2 associate-route-table \
            --subnet-id $SUBNET_2_ID \
            --route-table-id $ROUTE_TABLE_ID \
            --region $AWS_DEFAULT_REGION 2>/dev/null || log_warning "Subnet 2 already associated"
        log_success "Subnets associated with route table"
    fi
}

# Create security groups
create_security_groups() {
    print_header "Step 2: Creating Security Groups"
    
    # Backend security group
    EXISTING_BACKEND_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=corporatechat-backend-sg" "Name=vpc-id,Values=$VPC_ID" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)
    if [[ "$EXISTING_BACKEND_SG" != "None" ]] && [[ -n "$EXISTING_BACKEND_SG" ]]; then
        log_warning "Backend security group already exists: $EXISTING_BACKEND_SG"
        BACKEND_SG_ID=$EXISTING_BACKEND_SG
    else
        log_info "Creating backend security group..."
        BACKEND_SG_ID=$(aws ec2 create-security-group \
            --group-name corporatechat-backend-sg \
            --description "Security group for Corporate Chat backend" \
            --vpc-id $VPC_ID \
            --region $AWS_DEFAULT_REGION \
            --query 'GroupId' \
            --output text)
        log_success "Backend security group created: $BACKEND_SG_ID"
        
        # Allow port 80
        aws ec2 authorize-security-group-ingress \
            --group-id $BACKEND_SG_ID \
            --protocol tcp \
            --port 80 \
            --cidr 0.0.0.0/0 \
            --region $AWS_DEFAULT_REGION 2>/dev/null || log_warning "Port 80 rule already exists"
        log_success "Port 80 allowed on backend security group"
    fi
    
    # Frontend security group
    EXISTING_FRONTEND_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=corporatechat-frontend-sg" "Name=vpc-id,Values=$VPC_ID" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)
    if [[ "$EXISTING_FRONTEND_SG" != "None" ]] && [[ -n "$EXISTING_FRONTEND_SG" ]]; then
        log_warning "Frontend security group already exists: $EXISTING_FRONTEND_SG"
        FRONTEND_SG_ID=$EXISTING_FRONTEND_SG
    else
        log_info "Creating frontend security group..."
        FRONTEND_SG_ID=$(aws ec2 create-security-group \
            --group-name corporatechat-frontend-sg \
            --description "Security group for Corporate Chat frontend" \
            --vpc-id $VPC_ID \
            --region $AWS_DEFAULT_REGION \
            --query 'GroupId' \
            --output text)
        log_success "Frontend security group created: $FRONTEND_SG_ID"
        
        # Allow port 80
        aws ec2 authorize-security-group-ingress \
            --group-id $FRONTEND_SG_ID \
            --protocol tcp \
            --port 80 \
            --cidr 0.0.0.0/0 \
            --region $AWS_DEFAULT_REGION 2>/dev/null || log_warning "Port 80 rule already exists"
        log_success "Port 80 allowed on frontend security group"
    fi
}

# Create IAM roles
create_iam_roles() {
    print_header "Step 3: Creating IAM Roles"
    
    # Check if role exists
    if aws iam get-role --role-name corporatechat-execution-role &>/dev/null; then
        log_warning "IAM role already exists: corporatechat-execution-role"
    else
        log_info "Creating ECS execution role..."
        
        # Create trust policy
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
        
        aws iam create-role \
            --role-name corporatechat-execution-role \
            --assume-role-policy-document file:///tmp/ecs-trust-policy.json \
            --region $AWS_DEFAULT_REGION
        
        # Attach managed policy
        aws iam attach-role-policy \
            --role-name corporatechat-execution-role \
            --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
            --region $AWS_DEFAULT_REGION
        
        log_success "IAM role created and policy attached"
        rm -f /tmp/ecs-trust-policy.json
    fi
}

# Create ECR repositories
create_ecr_repos() {
    print_header "Step 4: Creating ECR Repositories"
    
    # Backend repository
    if aws ecr describe-repositories --repository-names corporatechat-backend --region $AWS_DEFAULT_REGION &>/dev/null; then
        log_warning "Backend ECR repository already exists"
    else
        log_info "Creating backend ECR repository..."
        aws ecr create-repository \
            --repository-name corporatechat-backend \
            --region $AWS_DEFAULT_REGION
        log_success "Backend ECR repository created"
    fi
    
    # Frontend repository
    if aws ecr describe-repositories --repository-names corporatechat-frontend --region $AWS_DEFAULT_REGION &>/dev/null; then
        log_warning "Frontend ECR repository already exists"
    else
        log_info "Creating frontend ECR repository..."
        aws ecr create-repository \
            --repository-name corporatechat-frontend \
            --region $AWS_DEFAULT_REGION
        log_success "Frontend ECR repository created"
    fi
}

# Create CloudWatch log groups
create_log_groups() {
    print_header "Step 5: Creating CloudWatch Log Groups"
    
    # Backend log group
    if aws logs describe-log-groups --log-group-name-prefix /ecs/corporatechat-backend --region $AWS_DEFAULT_REGION | grep -q corporatechat-backend; then
        log_warning "Backend log group already exists"
    else
        log_info "Creating backend log group..."
        aws logs create-log-group \
            --log-group-name /ecs/corporatechat-backend \
            --region $AWS_DEFAULT_REGION
        log_success "Backend log group created"
    fi
    
    # Frontend log group
    if aws logs describe-log-groups --log-group-name-prefix /ecs/corporatechat-frontend --region $AWS_DEFAULT_REGION | grep -q corporatechat-frontend; then
        log_warning "Frontend log group already exists"
    else
        log_info "Creating frontend log group..."
        aws logs create-log-group \
            --log-group-name /ecs/corporatechat-frontend \
            --region $AWS_DEFAULT_REGION
        log_success "Frontend log group created"
    fi
}

# Create ECS cluster
create_ecs_cluster() {
    print_header "Step 6: Creating ECS Cluster"
    
    if aws ecs describe-clusters --clusters corporatechat-cluster --region $AWS_DEFAULT_REGION | grep -q "ACTIVE"; then
        log_warning "ECS cluster already exists"
    else
        log_info "Creating ECS cluster..."
        aws ecs create-cluster \
            --cluster-name corporatechat-cluster \
            --region $AWS_DEFAULT_REGION
        log_success "ECS cluster created"
    fi
}

# Build and push Docker images
build_and_push_images() {
    print_header "Step 7: Building and Pushing Docker Images"
    
    # Login to ECR
    log_info "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_DEFAULT_REGION | \
        sudo docker login --username AWS --password-stdin \
        ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com
    log_success "Logged in to ECR"
    
    # Build backend
    log_info "Building backend Docker image..."
    sudo docker build -f Dockerfile.backend -t corporatechat-backend:latest .
    log_success "Backend image built"
    
    # Tag and push backend
    log_info "Pushing backend image to ECR..."
    sudo docker tag corporatechat-backend:latest \
        ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-backend:latest
    sudo docker push \
        ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-backend:latest
    log_success "Backend image pushed to ECR"
}

# Deploy backend
deploy_backend() {
    print_header "Step 8: Deploying Backend"
    
    # Create task definition
    log_info "Creating backend task definition..."
    cat > /tmp/backend-task-def.json << EOF
{
  "family": "corporatechat-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/corporatechat-execution-role",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-backend:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "AWS_ACCESS_KEY_ID",
          "value": "${AWS_ACCESS_KEY_ID}"
        },
        {
          "name": "AWS_SECRET_ACCESS_KEY",
          "value": "${AWS_SECRET_ACCESS_KEY}"
        },
        {
          "name": "AWS_DEFAULT_REGION",
          "value": "${AWS_DEFAULT_REGION}"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/corporatechat-backend",
          "awslogs-region": "${AWS_DEFAULT_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF
    
    aws ecs register-task-definition \
        --cli-input-json file:///tmp/backend-task-def.json \
        --region $AWS_DEFAULT_REGION > /dev/null
    log_success "Backend task definition registered"
    rm -f /tmp/backend-task-def.json
    
    # Create or update service
    if aws ecs describe-services --cluster corporatechat-cluster --services corporatechat-backend --region $AWS_DEFAULT_REGION | grep -q "ACTIVE"; then
        log_warning "Backend service already exists, updating..."
        aws ecs update-service \
            --cluster corporatechat-cluster \
            --service corporatechat-backend \
            --force-new-deployment \
            --region $AWS_DEFAULT_REGION > /dev/null
        log_success "Backend service updated"
    else
        log_info "Creating backend service..."
        aws ecs create-service \
            --cluster corporatechat-cluster \
            --service-name corporatechat-backend \
            --task-definition corporatechat-backend \
            --desired-count 1 \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1_ID,$SUBNET_2_ID],securityGroups=[$BACKEND_SG_ID],assignPublicIp=ENABLED}" \
            --region $AWS_DEFAULT_REGION > /dev/null
        log_success "Backend service created"
    fi
    
    # Wait for task to start
    log_info "Waiting for backend task to start (60 seconds)..."
    sleep 60
    
    # Get backend IP
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
    
    log_success "Backend deployed at: http://$BACKEND_IP"
    
    # Test backend
    log_info "Testing backend health..."
    if curl -s http://$BACKEND_IP/health | grep -q "healthy"; then
        log_success "Backend health check passed"
    else
        log_warning "Backend health check failed, but continuing..."
    fi
}

# Build and deploy frontend
deploy_frontend() {
    print_header "Step 9: Deploying Frontend"
    
    # Update Dockerfile.frontend with backend IP
    log_info "Updating frontend configuration with backend IP: $BACKEND_IP"
    sed -i "s|ARG VITE_API_BASE_URL=.*|ARG VITE_API_BASE_URL=http://$BACKEND_IP|" Dockerfile.frontend
    
    # Build frontend
    log_info "Building frontend Docker image..."
    sudo docker build -f Dockerfile.frontend -t corporatechat-frontend:latest .
    log_success "Frontend image built"
    
    # Tag and push frontend
    log_info "Pushing frontend image to ECR..."
    sudo docker tag corporatechat-frontend:latest \
        ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-frontend:latest
    sudo docker push \
        ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-frontend:latest
    log_success "Frontend image pushed to ECR"
    
    # Create task definition
    log_info "Creating frontend task definition..."
    cat > /tmp/frontend-task-def.json << EOF
{
  "family": "corporatechat-frontend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/corporatechat-execution-role",
  "containerDefinitions": [
    {
      "name": "frontend",
      "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/corporatechat-frontend:latest",
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
          "awslogs-region": "${AWS_DEFAULT_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF
    
    aws ecs register-task-definition \
        --cli-input-json file:///tmp/frontend-task-def.json \
        --region $AWS_DEFAULT_REGION > /dev/null
    log_success "Frontend task definition registered"
    rm -f /tmp/frontend-task-def.json
    
    # Create or update service
    if aws ecs describe-services --cluster corporatechat-cluster --services corporatechat-frontend --region $AWS_DEFAULT_REGION | grep -q "ACTIVE"; then
        log_warning "Frontend service already exists, updating..."
        aws ecs update-service \
            --cluster corporatechat-cluster \
            --service corporatechat-frontend \
            --force-new-deployment \
            --region $AWS_DEFAULT_REGION > /dev/null
        log_success "Frontend service updated"
    else
        log_info "Creating frontend service..."
        aws ecs create-service \
            --cluster corporatechat-cluster \
            --service-name corporatechat-frontend \
            --task-definition corporatechat-frontend \
            --desired-count 1 \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1_ID,$SUBNET_2_ID],securityGroups=[$FRONTEND_SG_ID],assignPublicIp=ENABLED}" \
            --region $AWS_DEFAULT_REGION > /dev/null
        log_success "Frontend service created"
    fi
    
    # Wait for task to start
    log_info "Waiting for frontend task to start (60 seconds)..."
    sleep 60
    
    # Get frontend IP
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
    
    log_success "Frontend deployed at: http://$FRONTEND_IP"
}

# Print final summary
print_summary() {
    print_header "DEPLOYMENT COMPLETE!"
    
    echo -e "${GREEN}Your Corporate Chat application is now deployed!${NC}"
    echo ""
    echo -e "${BLUE}Access URLs:${NC}"
    echo -e "  Frontend: ${GREEN}http://$FRONTEND_IP${NC}"
    echo -e "  Backend:  ${GREEN}http://$BACKEND_IP${NC}"
    echo ""
    echo -e "${BLUE}AWS Resources:${NC}"
    echo -e "  VPC:               $VPC_ID"
    echo -e "  Subnets:           $SUBNET_1_ID, $SUBNET_2_ID"
    echo -e "  Security Groups:   $BACKEND_SG_ID (backend), $FRONTEND_SG_ID (frontend)"
    echo -e "  ECS Cluster:       corporatechat-cluster"
    echo -e "  ECR Repositories:  corporatechat-backend, corporatechat-frontend"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Access the application at: http://$FRONTEND_IP"
    echo "  2. Monitor logs: aws logs tail /ecs/corporatechat-backend --follow"
    echo "  3. Check the DEPLOYMENT.md file for troubleshooting and maintenance"
    echo ""
    echo -e "${YELLOW}Note:${NC} ECS Fargate tasks use dynamic IPs. If tasks restart, IPs may change."
    echo "See DEPLOYMENT.md for instructions on handling IP changes."
    echo ""
}

# Main execution
main() {
    print_header "Corporate Chat - AWS ECS Deployment"
    echo "This script will deploy the Corporate Chat application to AWS ECS Fargate"
    echo ""
    
    check_prerequisites
    create_vpc
    create_security_groups
    create_iam_roles
    create_ecr_repos
    create_log_groups
    create_ecs_cluster
    build_and_push_images
    deploy_backend
    deploy_frontend
    print_summary
}

# Run main function
main
