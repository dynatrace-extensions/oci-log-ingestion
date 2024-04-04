import io
import os
import json
import requests
import logging

LOG_INGEST_ENDPOINT = "/api/v2/logs/ingest"

def process_log_line(body):
    try:
        logging.getLogger().info(f"Body: {body}")
        data = body.get("data", {})
        source = body.get("source")
        time = body.get("time")

        request_body = {}
        request_body["log.source"] = source
        request_body["timestamp"] = time
        request_body["content"] = data
        
        dynatrace_api_key = os.environ("DYNATRACE_API_KEY")
        tenant_url = os.environ("DYNATRACE_ENDPOINT")
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