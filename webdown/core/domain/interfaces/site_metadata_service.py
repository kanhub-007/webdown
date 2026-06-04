"""Domain service interface for site metadata discovery."""

from abc import ABC, abstractmethod


class SiteMetadataService(ABC):
    """Discovers common site metadata files."""

    @abstractmethod
    def check_site_metadata_files(self, base_url: str) -> dict[str, str]:
        """Check for common site metadata files."""
