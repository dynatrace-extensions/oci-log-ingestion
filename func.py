import io
import os
import json
import requests
import logging

LOG_INGEST_ENDPOINT = "/api/v2/logs/ingest"

def process_log_line(body):
    try:
        logging.getLogger().info(f"Body: {body}")
        source = body.get("source")
        time = body.get("time")

        data = body.get("data", {})
        # Pull fields out of the OCI body for use as Dynatrace attribute key/value pairs
        bucket_id = data.get("bucketId", "")
        bucket_name = data.get("bucketName", "")
        message = data.get("message", "")
        region = data.get("region", "")
        tenant_name = data.get("tenantName", "")
        tenant_id = data.get("tenantId", "")
        compartment_name = data.get("compartmentName", "")
        compartment_id = data.get("compartmentId", "")
        principal_name = data.get("principalName", "")
        principal_id = data.get("principalId", "")

        request_body = {
            "log.source": "Oracle Cloud Infrastructure",
            "timestamp": time,
            "content": message,
            "cloud.provider": "oci",
            "oci.bucket_id": bucket_id,
            "oci.bucket_name": bucket_name,
            "oci.region": region,
            "oci.tenant_name": tenant_name,
            "oci.tenant_id": tenant_id,
            "oci.compartment_name": compartment_name,
            "oci.compartment_id": compartment_id,
            "oci.principal_name": principal_name,
            "oci.principal_id": principal_id
        }
        
        dynatrace_api_key = os.environ["DYNATRACE_API_KEY"]
        tenant_url = os.environ["DYNATRACE_TENANT"]
        # Remove the trailing slash if it exits
        if tenant_url.endswith("/"):
            tenant_url = tenant_url[:-1]

        # Append the log ingest endpoint to tenant url
        tenant_url = f"{tenant_url}{LOG_INGEST_ENDPOINT}"

        headers = {"Content-Type": "application/json", "Authorization": f"Api-Token {dynatrace_api_key}"}
        response = requests.post(tenant_url, data = json.dumps(request_body), headers=headers) 
        logging.getLogger().info(response.text)

    except (Exception, ValueError) as ex:
        logging.getLogger().error(str(ex))

"""
This function receives the logging json and invokes the Datadog endpoint for ingesting logs. https://docs.cloud.oracle.com/en-us/iaas/Content/Logging/Reference/top_level_logging_format. htm#top_level_logging_format
If this Function is invoked with more than one log the function go over each log and invokes the endpoint for ingesting one by one.
"""
def handler(ctx, data: io.BytesIO=None):
    try:
        body = json.loads(data.getvalue())
        if isinstance(body, list):
            # Batch of CloudEvents format
            for b in body:
                process_log_line(b)
        else:
            # Single CloudEvent
            process_log_line(body)
    except (Exception, ValueError) as ex:
        logging.getLogger().error(str(ex))