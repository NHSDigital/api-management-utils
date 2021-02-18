variable "profile" {
  type = string
}

terraform {
  backend "s3" {
    key            = "pre-reqs/terraform.tfstate"
    region  = "eu-west-2"
    encrypt = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region  = "eu-west-2"
  profile = var.profile
}


