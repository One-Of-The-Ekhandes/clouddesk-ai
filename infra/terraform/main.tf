locals {
  name = "clouddesk-ai"
}

data "aws_caller_identity" "current" {}

# ---------------------------------------------------------------- secret

resource "aws_ssm_parameter" "llm_key" {
  count       = var.llm_api_key == "" ? 0 : 1
  name        = "/${local.name}/llm-api-key"
  description = "LLM provider API key for CloudDesk AI"
  type        = "SecureString"
  value       = var.llm_api_key
}

# ---------------------------------------------------------------- IAM (least privilege)

data "aws_iam_policy_document" "assume_lambda" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${local.name}-lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}

data "aws_iam_policy_document" "lambda" {
  statement {
    sid       = "WriteOwnLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.lambda.arn}:*"]
  }

  dynamic "statement" {
    for_each = var.llm_api_key == "" ? [] : [1]
    content {
      sid       = "ReadLlmKey"
      actions   = ["ssm:GetParameter"]
      resources = [aws_ssm_parameter.llm_key[0].arn]
    }
  }

  statement {
    sid = "ReadOnlyIamChecks"
    actions = [
      "iam:GetUser",
      "iam:ListUsers",
      "iam:ListGroups",
      "iam:ListGroupsForUser",
      "iam:ListAttachedUserPolicies",
      "iam:ListAttachedGroupPolicies",
      "iam:ListMFADevices",
      "iam:SimulatePrincipalPolicy",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "${local.name}-lambda"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda.json
}

# ---------------------------------------------------------------- Lambda

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../build/lambda"
  output_path = "${path.module}/../build/lambda.zip"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.name}"
  retention_in_days = 7
}

resource "aws_lambda_function" "api" {
  function_name    = local.name
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "clouddesk.lambda_handler.handler"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  memory_size      = 512
  timeout          = 29
  architectures    = ["x86_64"]

  environment {
    variables = {
      LLM_PROVIDER  = var.llm_provider
      LLM_KEY_PARAM = var.llm_api_key == "" ? "" : aws_ssm_parameter.llm_key[0].name
      CLOUDDESK_DB  = "/tmp/clouddesk.db"
      IAM_SOURCE    = "snapshot"
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda, aws_iam_role_policy.lambda]
}

# ---------------------------------------------------------------- API Gateway (HTTP API)

resource "aws_apigatewayv2_api" "http" {
  name          = local.name
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true

  # Throttle hard: this is a public demo running on free-tier limits.
  default_route_settings {
    throttling_burst_limit = 5
    throttling_rate_limit  = 2
  }
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

# ---------------------------------------------------------------- cost guardrail

resource "aws_budgets_budget" "monthly" {
  name         = "${local.name}-monthly"
  budget_type  = "COST"
  limit_amount = var.monthly_budget_usd
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_email]
  }
}
