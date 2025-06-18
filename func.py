import io
import os
import json
import logging
from typing import Dict, Optional

from dynatrace_client import DynatraceClient
from urllib.parse import quote

from dynatrace_client import DynatraceClient

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
        
        tenant_url = os.environ["DYNATRACE_TENANT"]
        # Remove the trailing slash if it exits
        if tenant_url.endswith("/"):
            tenant_url = tenant_url[:-1]
        client = DynatraceClient(tenant_url)

        auth_method = os.environ["AUTH_METHOD"]
        if auth_method == "oauth":
            client_id = os.environ["OAUTH_CLIENT_ID"]
            client_secret = os.environ["OAUTH_CLIENT_SECRET"]
            account_urn = os.environ["OAUTH_ACCOUNT_URN"]
            client.using_oauth(client_id, client_secret, account_urn)
        elif auth_method == "token":
            api_token = os.environ["DYNATRACE_API_KEY"]
            client.using_api_token(api_token)
        else:
            logging.getLogger().error(f"Invalid authentication method '{auth_method}'. Expected either 'oauth' or 'token'")
        
        proxy_url = create_proxy_connection()
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        client.send_log(json.dumps(request_body), proxies)
    except (Exception, ValueError) as ex:
        logging.getLogger().error(str(ex))

def create_proxy_connection() -> Optional[Dict[str, str]]:
    proxy_address = os.environ.get("PROXY_URL", None)
    proxy_username = os.environ.get("PROXY_USERNAME", None)
    proxy_password = os.environ.get("PROXY_PASSWORD", None)

    if proxy_address is None:
        return None

    if proxy_address:
        protocol, address = proxy_address.split("://")
        proxy_url = f"{protocol}://"
        proxy_url += _create_user_pass_url(proxy_username, proxy_password)
        proxy_url += f"{address}"
        return proxy_url

    return None


def _create_user_pass_url(proxy_username: str, proxy_password: str) -> str:
    user_pass_url = None
    if proxy_username:
        proxy_username = quote(proxy_username, safe="")
        user_pass_url = proxy_username
        if proxy_password:
            proxy_password = quote(proxy_password, safe="")
            user_pass_url += f":{proxy_password}"
        user_pass_url += "@"
    return user_pass_url if user_pass_url else ""


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