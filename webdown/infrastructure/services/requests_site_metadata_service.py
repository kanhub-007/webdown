"""Site metadata discovery service backed by requests."""

from webdown.core.domain.interfaces.site_metadata_service import SiteMetadataService
from webdown.infrastructure.services.requests_sitemap_discovery_service import _check_site_metadata_files


class RequestsSiteMetadataService(SiteMetadataService):
    """Site metadata discovery service backed by requests."""

    def check_site_metadata_files(self, base_url: str) -> dict[str, str]:
        """Check for common site metadata files."""
        return _check_site_metadata_files(base_url)
