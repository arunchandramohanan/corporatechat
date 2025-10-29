# Corporate Chat - Quick Start Guide

## Current Deployment

**Frontend:** http://99.79.37.132  
**Backend API:** http://15.157.72.48:3009

Access your application at the frontend URL above.

## When Backend IP Changes

Whenever you redeploy the backend or it restarts, run this command:

```bash
./update-frontend-backend-url.sh
```

This script will:
1. Get the current backend IP
2. Update the frontend configuration
3. Redeploy the frontend
4. Show you the new URLs

**That's it!** One command fixes the IP change issue.

## Common Operations

### View Current Deployment Info
```bash
source deployment-info.sh
echo "Frontend: $FRONTEND_URL"
echo "Backend: $BACKEND_URL"
```

### Check Service Status
```bash
aws ecs describe-services \
  --cluster corporatechat-cluster \
  --services corporatechat-frontend corporatechat-backend \
  --region ca-central-1 \
  --query 'services[*].{Name:serviceName,Running:runningCount,Desired:desiredCount}'
```

### View Backend Logs
```bash
aws logs tail /ecs/corporatechat-backend --follow --region ca-central-1
```

### View Frontend Logs
```bash
aws logs tail /ecs/corporatechat-frontend --follow --region ca-central-1
```

### Rebuild and Redeploy Backend
```bash
# 1. Make code changes
# 2. Rebuild image
sudo docker build -f Dockerfile.backend -t corporatechat-backend:latest .

# 3. Push to ECR
sudo docker tag corporatechat-backend:latest 502027401191.dkr.ecr.ca-central-1.amazonaws.com/corporatechat-backend:latest
sudo docker push 502027401191.dkr.ecr.ca-central-1.amazonaws.com/corporatechat-backend:latest

# 4. Update ECS service
aws ecs update-service \
  --cluster corporatechat-cluster \
  --service corporatechat-backend \
  --force-new-deployment \
  --region ca-central-1

# 5. Update frontend with new backend IP
./update-frontend-backend-url.sh
```

### Rebuild and Redeploy Frontend
```bash
# 1. Make code changes
# 2. Rebuild image
sudo docker build -f Dockerfile.frontend -t corporatechat-frontend:latest .

# 3. Push to ECR
sudo docker tag corporatechat-frontend:latest 502027401191.dkr.ecr.ca-central-1.amazonaws.com/corporatechat-frontend:latest
sudo docker push 502027401191.dkr.ecr.ca-central-1.amazonaws.com/corporatechat-frontend:latest

# 4. Update ECS service
aws ecs update-service \
  --cluster corporatechat-cluster \
  --service corporatechat-frontend \
  --force-new-deployment \
  --region ca-central-1
```

## Cleanup (Delete Everything)
```bash
./cleanup-aws.sh
```

## Files Reference

- `update-frontend-backend-url.sh` - **Use this when backend IP changes**
- `deploy-ecs-public-ip.sh` - Full deployment script
- `deployment-info.sh` - Current IPs and URLs
- `infrastructure-config.sh` - AWS resource IDs
- `cleanup-aws.sh` - Delete all AWS resources

## Cost Estimate

**Current setup:**
- ECS Fargate (2 tasks): ~$30-40/month
- Data transfer: ~$5-10/month
- CloudWatch logs: ~$5/month
- **Total: ~$40-55/month**

## Troubleshooting

### Frontend can't connect to backend
```bash
# Run the update script
./update-frontend-backend-url.sh
```

### Backend not responding
```bash
# Check backend logs
aws logs tail /ecs/corporatechat-backend --since 5m --region ca-central-1

# Check backend is running
curl http://15.157.72.48:3009/health
```

### Need to restart everything
```bash
# Restart both services
aws ecs update-service --cluster corporatechat-cluster --service corporatechat-backend --force-new-deployment --region ca-central-1
aws ecs update-service --cluster corporatechat-cluster --service corporatechat-frontend --force-new-deployment --region ca-central-1

# Wait 2 minutes, then update frontend with new backend IP
sleep 120
./update-frontend-backend-url.sh
```

## Support

- Logs location: CloudWatch → `/ecs/corporatechat-backend` and `/ecs/corporatechat-frontend`
- Region: ca-central-1 (Canada Central)
- Account: 502027401191

---

**Last Updated:** $(date)
