
terraform {
  backend "s3" {
    key            = "pre-reqs/terraform.tfstate"
    region         = "eu-west-2"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region  = "eu-west-2"
  profile = var.profile
}

data "terraform_remote_state" "account" {
  backend   = "s3"
  workspace = "management:${var.account}"

  config = {
    profile = var.profile
    key     = "account/terraform.tfstate"
    region  = "eu-west-2"
    bucket  = var.state_bucket
    encrypt = true
  }
}
