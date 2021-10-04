locals {
  project_postfix = "tst-1"
}

provider "aws" {
  region = "eu-central-1"
  shared_credentials_file = "~/.aws/creds"
  profile = "ersotech_aws_tst_1"
}

terraform {
  backend "s3" {
    bucket = "terraform-shared-state-ersotech-aws-tst-1"
    key = "terraform/the_bot_it_state"
    region = "eu-central-1"
    shared_credentials_file = "~/.aws/creds"
    profile = "ersotech_aws_tst_1"
  }
}

module "the_bot_it_common" {
    source = "../modules/the_bot_it_common"
    environment = local.project_postfix
}

output "code_uploader_bucket_name" {
    value = module.the_bot_it_common.code_uploader_bucket_name
}

output "code_uploader_id" {
    value = module.the_bot_it_common.code_uploader_id
}

output "code_uploader_secret" {
    value = module.the_bot_it_common.code_uploader_secret
}
