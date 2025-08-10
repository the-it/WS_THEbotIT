locals {
  module_name = "ws_bot"
}

resource "aws_dynamodb_table" "manage_table" {
  name           = "wiki_bots_manage_table_${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "bot_name"
  range_key      = "start_time"

  attribute {
    name = "bot_name"
    type = "S"
  }

  attribute {
    name = "start_time"
    type = "S"
  }
}

resource "aws_s3_bucket" "state_bucket" {
  bucket = "wiki-bots-persisted-data-${var.environment}"
  tags = {
    "project" = local.module_name
    "environment" = var.environment
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "encryption" {
  bucket = aws_s3_bucket.state_bucket.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_logging" "logging_state_bucket" {
  bucket = aws_s3_bucket.state_bucket.id

  target_bucket = var.logging_bucket
  target_prefix = "log/${aws_s3_bucket.state_bucket.id}/"
}

resource "aws_iam_user" "ws_bot_user" {
  name = "ws_bot_user_${var.environment}"
}

data "aws_iam_policy_document" "ws_bot_bucket_policy_document" {
  statement {
    actions = [
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.state_bucket.arn,
    ]
  }

  statement {
    actions = [
      "s3:*",
    ]

    resources = [
      "${aws_s3_bucket.state_bucket.arn}/*",
    ]
  }
}

resource "aws_iam_user_policy" "ws_bot_bucket_policy" {
  name   = "ws_bot_bucket_policy"
  user   = aws_iam_user.ws_bot_user.name
  policy = data.aws_iam_policy_document.ws_bot_bucket_policy_document.json
}

data "aws_iam_policy_document" "ws_bot_table_policy_document" {
  statement {
    actions = [
      "dynamodb:List*",
    ]

    resources = [
      "*",
    ]
  }

  statement {
    actions = [
      "dynamodb:*",
    ]

    resources = [
      aws_dynamodb_table.manage_table.arn,
    ]
  }
}

resource "aws_iam_user_policy" "ws_bot_table_policy" {
  name   = "ws_bot_table_policy"
  user   = aws_iam_user.ws_bot_user.name
  policy = data.aws_iam_policy_document.ws_bot_table_policy_document.json
}