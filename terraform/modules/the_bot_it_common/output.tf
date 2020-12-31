output "code_uploader_bucket_name" {
  value = aws_s3_bucket.code_bucket.bucket
}

output "code_uploader_secret" {
  value = aws_iam_access_key.user_code_uploader_keys.secret
}

output "code_uploader_id" {
  value = aws_iam_access_key.user_code_uploader_keys.id
}