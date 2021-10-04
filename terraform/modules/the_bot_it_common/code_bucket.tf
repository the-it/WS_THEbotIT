resource "aws_s3_bucket" "code_bucket" {
    bucket = "the-bot-it-code-${var.environment}"
    tags = {
        "project" = local.module_name
        "environment" = var.environment
    }
    logging {
        target_bucket = "logging-${var.environment}"
        target_prefix = "${local.module_name}/"
    }
    server_side_encryption_configuration {
        rule {
            apply_server_side_encryption_by_default {
                sse_algorithm = "AES256"
            }
        }
    }
}

resource "aws_s3_bucket_public_access_block" "code_bucket_public_block" {
    bucket = aws_s3_bucket.code_bucket.id

    block_public_acls = true
    block_public_policy = true
    ignore_public_acls = true
    restrict_public_buckets = true
}

resource "aws_iam_user" "user_code_uploader" {
    name = "${local.module_name}_code_uploader_${var.environment}"
}

resource "aws_iam_access_key" "user_code_uploader_keys" {
    user = aws_iam_user.user_code_uploader.name
}

data "aws_iam_policy_document" "code_uploader_policy_data" {
    statement {
        sid = "PutCodeToBucket"
        actions = [
            "s3:PutObject",
            "s3:GetObject",
        ]

        resources = [
            "${aws_s3_bucket.code_bucket.arn}/*",
        ]
    }
    statement {
        sid = "UpdateLambdaFunction"
        actions = [
            "lambda:UpdateFunctionCode",
        ]

        resources = [
            "*",
        ]
    }
}

resource "aws_iam_user_policy" "backup_nas_policy" {
    name = "code_uploader_policy"
    user = aws_iam_user.user_code_uploader.name

    policy = data.aws_iam_policy_document.code_uploader_policy_data.json
}

