from google.cloud import secretmanager


class SecretManager:
    def __init__(
        self,
        project_id: str,
    ) -> None:
        self.project_id = project_id
        self.gcp_client = secretmanager.SecretManagerServiceClient()

    def get_secret(self, secret_name: str) -> str:
        response = self.gcp_client.access_secret_version(request={"name": secret_name})
        return response.payload.data.decode("UTF-8").strip()
