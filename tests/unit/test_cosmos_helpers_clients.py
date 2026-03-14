import builtins
from unittest import mock

from shared import cosmos_helpers


def test_sync_cosmos_client_singleton():
    with mock.patch.object(cosmos_helpers, "CosmosClient") as mock_client_cls, mock.patch.object(
        cosmos_helpers, "DefaultAzureCredential"
    ):
        instance1 = cosmos_helpers._get_sync_cosmos_client()
        instance2 = cosmos_helpers._get_sync_cosmos_client()

    mock_client_cls.assert_called_once()
    assert instance1 is instance2


def test_async_cosmos_client_singleton():
    with mock.patch.object(cosmos_helpers, "CosmosClientAio") as mock_client_cls, mock.patch.object(
        cosmos_helpers, "DefaultAzureCredential"
    ):
        instance1 = cosmos_helpers._get_async_cosmos_client()
        instance2 = cosmos_helpers._get_async_cosmos_client()

    mock_client_cls.assert_called_once()
    assert instance1 is instance2

