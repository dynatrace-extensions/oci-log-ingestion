from abc import abstractmethod, ABC
import logging
import time
from typing import Dict
import requests

LOG_INGEST_ENDPOINT = "/api/v2/logs/ingest"
OAUTH_TOKEN_ENDPOINT = "/sso/oauth2/token"


class BaseClient(ABC):
    @abstractmethod
    def send_log(self, body: str):
        pass


class OAuthClient(BaseClient):
    def __init__(self, tenant: str, client_id: str, client_secret: str, urn: str):
        self._tenant = tenant
        self._client_id = client_id
        self._client_secret = client_secret
        self._urn = urn
        self._expiration = -1
        self._access_token = None

    def is_expired(self):
        return self._expiration == -1 or self._expiration >= time.time()

    def refresh_token(self):
        if self._access_token is None or self.is_expired():
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "resource": self._urn,
                "scope": "storage:metrics:write",
            }
            response = requests.post(
                "https://sso.dynatrace.com/sso/oauth2/token", data=data, headers=headers
            )
            if response.status_code == 200:
                json = response.json()
                self._expiration = time.time() + json.get("expires_in")
                self._access_token = json.get("access_token")
            else:
                logging.getLogger().error(
                    f"Could not authentication using OAuth: {response.text}"
                )

    def send_log(self, body: str, proxies: Dict[str, str]):
        self.refresh_token()
        try:
            tenant_url = f"{self._tenant}{LOG_INGEST_ENDPOINT}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._access_token}",
            }
            response = requests.post(tenant_url, data=body, headers=headers, proxies=proxies)
            logging.getLogger().info(response.json())
        except Exception as e:
            logging.getLogger().error(f"Error sending mint metric: {e}")


class ApiClient(BaseClient):
    def __init__(self, tenant: str, api_token: str):
        self._tenant = tenant
        self._api_token = api_token

    def send_log(self, body: str, proxies: Dict[str, str]):
        try:
            tenant_url = f"{self._tenant}{LOG_INGEST_ENDPOINT}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Api-Token {self._api_token}",
            }
            response = requests.post(tenant_url, data=body, headers=headers, proxies=proxies)
            logging.getLogger().info(response.text)
        except Exception as e:
            logging.getLogger().error(f"Error sending mint metric: {e}")


class DynatraceClient:
    def __init__(self, tenant: str):
        self._tenant = tenant

    def using_oauth(self, client_id: str, client_secret: str, urn: str):
        self._client = OAuthClient(self._tenant, client_id, client_secret, urn)
        return self

    def using_api_token(self, api_token: str):
        self._client = ApiClient(self._tenant, api_token)
        return self

    def send_log(self, body: str, proxies: Dict[str, str]):
        self._client.send_log(body, proxies)
