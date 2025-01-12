resource "google_spanner_instance" "spanner_instance" {
  config       = var.spanner_instance_config
  display_name = var.spanner_instance_display_name
  autoscaling_config {
    autoscaling_limits {
      max_processing_units = 2000
      min_processing_units = 1000
    }
    autoscaling_targets {
      high_priority_cpu_utilization_percent = 75
      storage_utilization_percent           = 90
    }
  }
  labels = {
    env = var.environment
  }
}


resource "google_spanner_database" "database" {
  instance = google_spanner_instance.spanner_instance.name
  name     = var.database_name
  deletion_protection = false
}

