terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.7"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project   = "clouddesk-ai"
      ManagedBy = "terraform"
      Owner     = var.owner
    }
  }
}
