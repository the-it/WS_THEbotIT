variable "environment" {
    type    = string
}

variable "cron_schedule" {
    type    = string
    default = "cron(01 01 1 1 ? 2099)"
}
