######################
# VPC + Subnets
######################

resource "aws_vpc" "queueescape" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "queueescape-vpc"
  }
}

resource "aws_internet_gateway" "queueescape_igw" {
  vpc_id = aws_vpc.queueescape.id

  tags = {
    Name = "queueescape-igw"
  }
}

######################
# Public Subnets (for NAT Gateway)
######################

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.queueescape.id
  cidr_block              = "10.0.0.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "queueescape-public-a"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.queueescape.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = {
    Name = "queueescape-public-b"
  }
}

# Route table for public subnet → Internet Gateway
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.queueescape.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.queueescape_igw.id
  }

  tags = {
    Name = "queueescape-public-rt"
  }
}

resource "aws_route_table_association" "public_a_assoc" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b_assoc" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

######################
# Private Subnets (for Lambda)
######################

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.queueescape.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "queueescape-private-a"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.queueescape.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "us-east-1b"

  tags = {
    Name = "queueescape-private-b"
  }
}

######################
# NAT Gateway for Private Subnets
######################

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "queueescape-nat-eip"
  }
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_a.id

  depends_on = [aws_internet_gateway.queueescape_igw]

  tags = {
    Name = "queueescape-nat"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.queueescape.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }

  tags = {
    Name = "queueescape-private-rt"
  }
}

resource "aws_route_table_association" "private_a_assoc" {
  subnet_id      = aws_subnet.private_a.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_b_assoc" {
  subnet_id      = aws_subnet.private_b.id
  route_table_id = aws_route_table.private.id
}

######################
# VPC Endpoints
######################

# DynamoDB VPC Endpoint (Gateway Type)
resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.queueescape.id
  service_name      = "com.amazonaws.us-east-1.dynamodb"
  vpc_endpoint_type = "Gateway"

  route_table_ids = [
    aws_route_table.private.id
  ]

  tags = {
    Name = "queueescape-dynamodb-endpoint"
  }
}

# SNS VPC Endpoint (Interface Type)
resource "aws_vpc_endpoint" "sns" {
  vpc_id            = aws_vpc.queueescape.id
  service_name      = "com.amazonaws.us-east-1.sns"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id
  ]

  security_group_ids = [
    aws_security_group.vpc_endpoint_sg.id
  ]

  private_dns_enabled = true

  tags = {
    Name = "queueescape-sns-endpoint"
  }
}

# STS VPC Endpoint (Interface Type) - Required for IAM role assumption
resource "aws_vpc_endpoint" "sts" {
  vpc_id            = aws_vpc.queueescape.id
  service_name      = "com.amazonaws.us-east-1.sts"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id
  ]

  security_group_ids = [
    aws_security_group.vpc_endpoint_sg.id
  ]

  private_dns_enabled = true

  tags = {
    Name = "queueescape-sts-endpoint"
  }
}

# Secrets Manager VPC Endpoint (Interface Type) - Optional but recommended
resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id            = aws_vpc.queueescape.id
  service_name      = "com.amazonaws.us-east-1.secretsmanager"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id
  ]

  security_group_ids = [
    aws_security_group.vpc_endpoint_sg.id
  ]

  private_dns_enabled = true

  tags = {
    Name = "queueescape-secretsmanager-endpoint"
  }
}

######################
# Outputs
######################

output "vpc_id" {
  value       = aws_vpc.queueescape.id
  description = "VPC ID"
}

output "private_subnet_ids" {
  value       = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  description = "Private subnet IDs for Lambda"
}

output "lambda_security_group_id" {
  value       = aws_security_group.lambda_sg.id
  description = "Security group ID for Lambda functions"
}