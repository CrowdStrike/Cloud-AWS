# Root-level sensor fetch. Runs once on the workstation via uv run, drops
# the RPM + result.json into a local cache; both modules consume the fetched
# CID + RPM path via the BYO inputs. Avoids unnecessary Falcon API traffic
# when the cache is already populated.
#
# depends_on on the data source is load-bearing: when count = 0 it's a no-op
# empty-list reference; when count = 1 it defers the data source's read from
# plan time to apply time, which is required on a fresh clone where the
# cache file doesn't exist yet.

locals {
  sensor_fetch_out_dir = "${path.module}/.sensor-cache"
  sensor_fetch_result  = "${local.sensor_fetch_out_dir}/result.json"
  cache_exists         = fileexists(local.sensor_fetch_result)
}

resource "null_resource" "fetch_sensor" {
  count = local.cache_exists ? 0 : 1

  triggers = {
    inputs_hash = sha256("${var.falcon_client_id}:${var.falcon_cloud}")
    script      = filemd5("${path.module}/../../scripts/fetch_sensor.py")
  }

  provisioner "local-exec" {
    command = join(" ", [
      "mkdir -p '${local.sensor_fetch_out_dir}' &&",
      "uv run '${path.module}/../../scripts/fetch_sensor.py'",
      "--out '${local.sensor_fetch_out_dir}'",
      "--cloud '${var.falcon_cloud}'",
      "--arch x86_64",
    ])

    environment = {
      FALCON_CLIENT_ID     = var.falcon_client_id
      FALCON_CLIENT_SECRET = var.falcon_client_secret
    }
  }
}

data "local_file" "sensor_fetch" {
  filename   = local.sensor_fetch_result
  depends_on = [null_resource.fetch_sensor]
}

locals {
  sensor_fetch_data = jsondecode(data.local_file.sensor_fetch.content)
  fetched_cid       = local.sensor_fetch_data.cid
  fetched_rpm_path  = local.sensor_fetch_data.rpm_path
}
