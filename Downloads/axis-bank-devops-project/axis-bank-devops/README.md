# Axis Bank–Style DevOps Banking Demo

> **Educational project only.** This is not an official Axis Bank application and is not affiliated with Axis Bank. Do not use real customer data, real credentials, or real money.

A small REST API for practicing end-to-end DevOps:

- Python + Flask REST API
- PostgreSQL database
- Pytest automated tests
- Git and GitHub workflow
- Docker + Docker Compose
- Kubernetes manifests for local Kubernetes and AWS EKS
- Terraform for AWS EKS, Amazon ECR, and GitHub Actions OIDC access
- GitHub Actions CI/CD
- AWS CloudWatch container logs through EKS/container logging can be added as a follow-up

## 1. Project flow

```text
Developer
   |
   | git push
   v
GitHub repository
   |
   v
GitHub Actions
   |-- install dependencies
   |-- run pytest
   |-- build Docker image
   |
   | on push to main, after CI succeeds
   v
AWS OIDC role
   |
   v
Amazon ECR ---> Amazon EKS ---> Axis Bank demo API
                    |
                    +---- PostgreSQL StatefulSet + persistent volume
```

## 2. Features

- Register a demo customer and create an account with a zero balance
- Login and receive a short-lived JWT access token
- View your account and balance
- Deposit demo funds
- Withdraw funds with insufficient-balance validation
- Transfer funds to another demo account
- View the latest 100 transactions
- Health endpoint for container and Kubernetes probes

This project is for DevOps practice, not a production banking system. Real banking requires professional security review, audit controls, compliance, reconciliation, fraud controls, stronger transaction/idempotency design, migrations, backups, and operational procedures.

## 3. Requirements

Install:
- Python 3.12+
- Git
- Docker Desktop (Windows/macOS) or Docker Engine (Linux)
- VS Code (recommended)

For Kubernetes practice, install **one** of:
- Docker Desktop Kubernetes
- Minikube
- kind

For AWS deployment:
- An AWS account with permission to create EKS, EC2, ECR, IAM, VPC, and EBS resources
- Terraform 1.6+
- AWS CLI v2
- kubectl

**AWS cost warning:** EKS, EC2 worker nodes, and EBS volumes can incur charges even when you are not actively using the application. Review AWS pricing, use a learning budget, and run `terraform destroy` when finished. Do not destroy infrastructure while you need its data.

## 4. Run locally with Python

Open a terminal in this project folder.

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
export DATABASE_URL="sqlite:///axis_bank.db"
export JWT_SECRET_KEY="change-this-local-demo-secret"
python -m pytest -q
python wsgi.py
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:DATABASE_URL = "sqlite:///axis_bank.db"
$env:JWT_SECRET_KEY = "change-this-local-demo-secret"
python -m pytest -q
python wsgi.py
```

Open `http://127.0.0.1:5000/health`. Expected response:

```json
{"application":"axis-bank-demo","status":"healthy"}
```

The app defaults to SQLite for quick tests. Docker Compose uses PostgreSQL.

## 5. Run with Docker Compose

Copy `.env.example` to `.env` and change the demo secrets first.

```bash
docker compose up --build
```

Check:

```bash
curl http://localhost:5000/health
```

Stop the containers:

```bash
docker compose down
```

The database data is stored in the Docker volume `postgres_data`. To remove the database volume too (this deletes the demo data):

```bash
docker compose down -v
```

Never commit `.env`.

## 6. Try the API

The API uses a JWT token for account actions.

### Register two demo users

```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Demo Customer One","email":"one@example.test","password":"DemoPass123!"}'
```

```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Demo Customer Two","email":"two@example.test","password":"DemoPass123!"}'
```

Save each returned `account_number`.

### Login

```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"one@example.test","password":"DemoPass123!"}'
```

Copy the returned `access_token`. In the examples below, replace `YOUR_TOKEN` with that token.

### View account and balance

```bash
curl http://localhost:5000/api/account \
  -H "Authorization: Bearer YOUR_TOKEN"

curl http://localhost:5000/api/balance \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Deposit demo funds

```bash
curl -X POST http://localhost:5000/api/deposit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"amount":"1000.00"}'
```

### Withdraw demo funds

```bash
curl -X POST http://localhost:5000/api/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"amount":"250.00"}'
```

### Transfer funds

Replace `AXIS_ACCOUNT_NUMBER_OF_USER_TWO` with the second user's account number.

```bash
curl -X POST http://localhost:5000/api/transfer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"to_account":"AXIS_ACCOUNT_NUMBER_OF_USER_TWO","amount":"100.00"}'
```

### Transaction history

```bash
curl http://localhost:5000/api/transactions \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 7. Git practice

Create an empty GitHub repository named `axis-bank-devops`, then run:

```bash
git init
git add .
git commit -m "Build Axis Bank demo API"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/axis-bank-devops.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME` with your GitHub username. Never commit `.env`, passwords, tokens, or AWS credentials.

Practice a change:

```bash
git checkout -b feature/transaction-validation
# edit the code
python -m pytest -q
git add .
git commit -m "Improve transaction validation"
git push -u origin feature/transaction-validation
```

Open a pull request to `main`. GitHub Actions runs tests and builds the Docker image.

## 8. Linux commands to practice

```bash
pwd                 # show current directory
ls -la              # list files, including hidden files
cd axis-bank-devops # change directory
cat README.md       # display a file
grep -R "health" .  # search files for text
ps aux              # list running processes
curl localhost:5000/health
docker ps           # list containers
docker logs <name>  # inspect container logs
```

Replace `<name>` with a real container name or ID.

## 9. Kubernetes practice locally

First build an image that your local Kubernetes environment can access.

### Minikube example

```bash
minikube start
minikube image build -t axis-bank-app:local .
kubectl create namespace axis-bank
kubectl create secret generic axis-bank-secrets \
  --from-literal=postgres-password=local-dev-password \
  --from-literal=jwt-secret-key=replace-this-local-secret \
  -n axis-bank
kubectl apply -f k8s/postgres-local.yaml
kubectl apply -f k8s/app.yaml
kubectl set image deployment/axis-bank-app app=axis-bank-app:local -n axis-bank
kubectl rollout status deployment/axis-bank-app -n axis-bank
kubectl get pods -n axis-bank
kubectl get services -n axis-bank
kubectl port-forward service/axis-bank-app 5000:80 -n axis-bank
```

In another terminal, open `http://localhost:5000/health`.

### Kubernetes commands to learn

```bash
kubectl get pods -n axis-bank
kubectl describe pod <pod-name> -n axis-bank
kubectl logs deployment/axis-bank-app -n axis-bank
kubectl get events -n axis-bank --sort-by=.metadata.creationTimestamp
kubectl rollout history deployment/axis-bank-app -n axis-bank
kubectl rollout undo deployment/axis-bank-app -n axis-bank
```

## 10. AWS infrastructure with Terraform

The Terraform configuration creates:
- VPC with public subnets for this learning setup
- EKS cluster and one small managed worker node
- ECR repository
- GitHub Actions OIDC provider and deploy role
- EKS access for that GitHub Actions role

**Learning-only network note:** To keep this starter simpler and avoid NAT Gateway charges, worker nodes are placed in public subnets. This is not the recommended production design. For production, use private worker nodes, private networking/endpoints or NAT as appropriate, restrict API access, and review IAM permissions.

### Configure Terraform

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
- `github_repository`: `YOUR_GITHUB_USERNAME/axis-bank-devops`
- `cluster_endpoint_public_access_cidrs`: replace the example IP with your current public IP in `/32` format
- keep the region consistent with your intended AWS region

Then:

```bash
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
```

Terraform will show outputs including the ECR repository URL and GitHub Actions role ARN.

### Configure GitHub repository settings

In GitHub, open **Settings → Secrets and variables → Actions**.

Add **repository variables**:
- `AWS_REGION` = your Terraform region, for example `ap-south-1`
- `ECR_REPOSITORY` = `axis-bank-app`
- `EKS_CLUSTER_NAME` = the cluster name from Terraform output (default: `axis-bank-demo-eks`)

Add **repository secrets**:
- `AWS_GITHUB_ACTIONS_ROLE_ARN` = Terraform output `github_actions_role_arn`
- `POSTGRES_PASSWORD` = a strong, unique demo password
- `JWT_SECRET_KEY` = a long random secret

The workflow uses GitHub OIDC rather than storing long-lived AWS access keys. The Terraform-created role is restricted to the specified repository's `main` branch. Review permissions before using this pattern in a real environment.

Push to `main`. The pipeline tests the code, builds and pushes an image to ECR, applies Kubernetes manifests, and updates the EKS deployment.

### Access the AWS deployment

After the pipeline succeeds, configure kubectl locally:

```bash
aws eks update-kubeconfig --region ap-south-1 --name axis-bank-demo-eks
kubectl get pods -n axis-bank
kubectl port-forward service/axis-bank-app 5000:80 -n axis-bank
```

Change the region/cluster name if you changed the Terraform values. Open `http://localhost:5000/health`.

## 11. Clean up AWS resources

When you have finished and no longer need the cluster:

```bash
kubectl delete namespace axis-bank
cd terraform
terraform destroy
```

Review the plan before confirming. Terraform destroy deletes the resources it manages; database contents on the persistent volume may be lost. Check the AWS Billing console afterward for any remaining resources.

## 12. Suggested practice tasks

1. Add a new API test and watch CI run.
2. Intentionally break a test, push a branch, and observe the pipeline fail.
3. Fix it and open a pull request.
4. Change a Dockerfile line and rebuild the image.
5. Use `kubectl logs`, `describe`, and `get events` to debug a failed pod.
6. Roll back a Kubernetes deployment.
7. Change a Terraform variable, inspect `terraform plan`, then apply.
8. Add an alert/log metric after the core deployment works.

## 13. Troubleshooting

- **Port 5000 is busy:** stop the process using it or change the host-side port in `docker-compose.yml`.
- **Database connection error in Compose:** run `docker compose ps` and `docker compose logs db app`.
- **Tests fail:** activate your virtual environment, run `pip install -r requirements.txt`, then `python -m pytest -q`.
- **Pod is `ImagePullBackOff`:** check the image name/tag, registry permissions, and `kubectl describe pod`.
- **Pod is `Pending`:** inspect PVCs and `kubectl describe pod`; the cluster may lack a suitable storage class or capacity.
- **GitHub deployment fails at AWS credentials:** check the OIDC role ARN, repo/branch trust policy, repository variables, and workflow permissions.
- **GitHub deployment fails at kubectl:** verify the EKS cluster name/region and that the role has an EKS access entry.
