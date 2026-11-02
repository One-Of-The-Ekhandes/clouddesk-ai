variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1" # Ireland
}

variable "owner" {
  description = "Owner tag applied to every resource"
  type        = string
  default     = "rujuta-ekhande"
}

variable "llm_provider" {
  description = "groq, gemini or mock"
  type        = string
  default     = "groq"
}

variable "llm_api_key" {
  description = "API key for the LLM provider, stored as an SSM SecureString"
  type        = string
  sensitive   = true
  default     = ""
}

variable "budget_email" {
  description = "Email address for the monthly budget alert"
  type        = string
}

variable "monthly_budget_usd" {
  description = "Alert when forecast or actual monthly spend passes this amount"
  type        = string
  default     = "1"
}
