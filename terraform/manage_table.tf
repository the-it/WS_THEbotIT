resource "aws_dynamodb_table" "basic-dynamodb-table" {
  name           = "wiki_bots_manage_table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "N"
  }
}
