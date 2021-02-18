

terraform {
  backend "s3" {
    key     = "deployment/terraform.tfstate"
    region  = "eu-west-2"
    encrypt = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region  = "eu-west-2"
  profile = var.profile
}


data "terraform_remote_state" "pre-reqs" {
  backend   = "s3"
  workspace = "api-deployment:${var.account}:${var.apigee_environment}:${var.service_id}"

  config = {
    profile = var.profile
    key     = "pre-reqs/terraform.tfstate"
    region  = "eu-west-2"
    bucket  = var.state_bucket
    encrypt = true
  }
}
