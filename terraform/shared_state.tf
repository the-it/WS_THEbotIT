terraform {
  backend "s3" {
    profile    = "default"
    bucket     = "ersotech-terraform-shared-state"
    key        = "wsthebotit.tfstate"
    region     = "eu-central-1"
    encrypt    = "true"
  }
}

