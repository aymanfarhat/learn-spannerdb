variable "project_id" {
  description = "The project ID to deploy resources to"
  type        = string
}

variable "region" {
  description = "The region to deploy resources to"
  type        = string
}

variable "spanner_instance_config" {
  description = "The Spanner instance configuration"
  type        = string
}

variable "spanner_instance_display_name" {
  description = "The Spanner instance display name"
  type        = string
}

variable "environment" {
  description = "The environment to deploy resources to"
  type        = string
}

variable "database_name" {
  description = "The name of the database"
  type        = string
}
