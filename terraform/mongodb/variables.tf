variable "mongodb_port" {
  description = "MongoDB Port"
  type        = number
  default     = 27017
}

variable "use_existing_mongodb" {
  description = "Use existing MongoDB installation if available"
  type        = bool
  default     = true
}