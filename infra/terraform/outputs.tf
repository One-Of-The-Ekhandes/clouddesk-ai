output "api_url" {
  description = "Base URL of the deployed CloudDesk API"
  value       = aws_apigatewayv2_api.http.api_endpoint
}

output "health_check" {
  value = "${aws_apigatewayv2_api.http.api_endpoint}/health"
}

output "lambda_function" {
  value = aws_lambda_function.api.function_name
}
