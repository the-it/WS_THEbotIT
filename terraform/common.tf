provider "aws" {
  region  = var.region
  profile = var.profile
}

data "aws_caller_identity" "current" {}
