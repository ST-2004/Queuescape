######################
# Lambda Security Group
######################

resource "aws_security_group" "lambda_sg" {
  name        = "queueescape-lambda-sg"
  description = "Security group for Lambda functions in private subnet"
  vpc_id      = aws_vpc.queueescape.id

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "queueescape-lambda-sg"
  }
}

######################
# VPC Endpoint Security Group
######################

resource "aws_security_group" "vpc_endpoint_sg" {
  name        = "queueescape-vpc-endpoint-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.queueescape.id

  # Allow inbound HTTPS from Lambda security group
  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda_sg.id]
    description     = "Allow HTTPS from Lambda"
  }

  # Allow inbound HTTPS from VPC CIDR (for private DNS resolution)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.queueescape.cidr_block]
    description = "Allow HTTPS from VPC CIDR"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "queueescape-vpc-endpoint-sg"
  }
}

######################
# Security Group Rules for Self-Reference
######################

# Allow Lambda SG to communicate with itself (for any Lambda-to-Lambda calls)
resource "aws_security_group_rule" "lambda_self_ingress" {
  type                     = "ingress"
  from_port                = 0
  to_port                  = 65535
  protocol                 = "-1"
  security_group_id        = aws_security_group.lambda_sg.id
  source_security_group_id = aws_security_group.lambda_sg.id
  description              = "Allow Lambda functions to communicate with each other"
}