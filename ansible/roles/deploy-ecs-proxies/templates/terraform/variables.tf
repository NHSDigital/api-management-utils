
variable "account" {
  type        = string
  description = "account (env) ptl/prod"
}

variable "profile" {
  type        = string
  description = "aws profile for remote state"
}

variable "workspace" {
  type        = string
  description = "terraform workspace required for management remote state"
}

variable "state_bucket" {
  type        = string
  description = "terraform state bucket"
}

variable "service_id" {
  type        = string
}

variable "apigee_environment" {
  type = string
}

variable "apigee_shortenv" {
  type = string
}

variable "namespace" {
  type        = string
}

variable "namespaced_name" {
  type        = string
}

variable "build_label" {
  type        = string
  description = "docker container label"
}

variable "min_desired_capacity" {
  type = number
  description = "initial desired capacity"
}

variable "autoscaling_enabled" {
  type = bool
}

variable "autoscaling_service_metric" {
  type = string
}

variable "autoscaling_target_value" {
  type = number
}

variable "autoscaling_scale_in_cooldown" {
  type = number
}

variable "autoscaling_scale_out_cooldown" {
  type = number
}

variable "deregistration_delay" {
  type = number
}

variable "use_ecs_tag" {
  type = bool
  description = "Whether to use ecs- prefixed tag for canary-api"
}