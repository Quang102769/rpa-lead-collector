"""Deduplication module for lead records.

Executes deterministic deduplication based on normalized company name and
verified digital identifiers (website domain, phone number).
"""

import copy
from collections import defaultdict
import re
import unicodedata
from urllib.parse import urlparse

from app.collectors.models import RawLeadRecord
from app.deduplication.models import (
    DeduplicationResult,
    DuplicateGroup,
    DuplicateReason,
)


class Deduplicator:
    """Deterministic deduplicator for batch lead processing.

    Enforces business matching rules without probabilistic or fuzzy logic:
    - Same normalized name + same normalized website -> Auto merge
    - Same normalized name + same normalized phone -> Auto merge
    - Different names with same website/phone -> Keep both
    - Same name lacking website and phone -> Keep both
    - Contradictory identifiers -> Keep both
    """

    _SCORED_FIELDS = (
        "company_name",
        "industry",
        "sub_industry",
        "source_url",
        "website",
        "public_email",
        "public_phone",
        "address",
        "province",
        "description",
        "collected_at",
    )

    # Valid domain structure with at least one dot and a 2+ char TLD
    _DOMAIN_REGEX = re.compile(
        r"^([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    )

    # Vietnam telecom numbering plans:
    # - Mobile (10 digits starting with 03, 05, 07, 08, 09)
    # - Landline (10 or 11 digits starting with 02)
    # - Hotlines (8 to 10 digits starting with 1800 or 1900)
    _VN_MOBILE_REGEX = re.compile(r"^0(3[2-9]|5[2-9]|7[0-9]|8[1-9]|9[0-9])[0-9]{7}$")
    _VN_LANDLINE_REGEX = re.compile(r"^02[0-9]{8,9}$")
    _VN_HOTLINE_REGEX = re.compile(r"^(1800|1900)[0-9]{4,6}$")

    def deduplicate(self, leads: list[RawLeadRecord]) -> DeduplicationResult:
        """Deduplicate a list of lead records deterministically.

        Args:
            leads: Input list of validated and normalized lead records.

        Returns:
            DeduplicationResult containing retained unique leads, duplicate groups,
            and verified metric counters.
        """
        if not leads:
            return DeduplicationResult(
                unique_records=[],
                duplicate_groups=[],
                total_processed=0,
            )

        # Ensure distinct object instances for each input position so object identity checks in DTOs hold
        processed_leads: list[RawLeadRecord] = []
        seen_obj_ids: set[int] = set()
        for lead in leads:
            if id(lead) in seen_obj_ids:
                processed_leads.append(copy.copy(lead))
            else:
                seen_obj_ids.add(id(lead))
                processed_leads.append(lead)
        leads = processed_leads

        n = len(leads)
        # Precompute normalized keys
        name_keys = [self.normalize_name(lead.company_name) for lead in leads]
        domain_keys = [self.normalize_website(lead.website) for lead in leads]
        phone_keys = [self.normalize_phone(lead.public_phone) for lead in leads]

        # Group indices by normalized company name (names must match for any merge)
        name_groups: dict[str, list[int]] = defaultdict(list)
        for idx, name_key in enumerate(name_keys):
            if name_key:
                name_groups[name_key].append(idx)
            else:
                # If name is missing (rare after validator), isolate record
                name_groups[f"__anonymous_{idx}__"].append(idx)

        # Disjoint Set Union (Union-Find)
        parent = list(range(n))

        def find(i: int) -> int:
            path = []
            curr = i
            while parent[curr] != curr:
                path.append(curr)
                curr = parent[curr]
            for node in path:
                parent[node] = curr
            return curr

        def union(i: int, j: int) -> None:
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_i] = root_j

        # Check duplicates only within the same normalized company name
        for indices in name_groups.values():
            if len(indices) <= 1:
                continue

            for idx_a_pos in range(len(indices)):
                idx_a = indices[idx_a_pos]
                for idx_b_pos in range(idx_a_pos + 1, len(indices)):
                    idx_b = indices[idx_b_pos]
                    if self._is_duplicate_pair(
                        domain_a=domain_keys[idx_a],
                        domain_b=domain_keys[idx_b],
                        phone_a=phone_keys[idx_a],
                        phone_b=phone_keys[idx_b],
                    ):
                        union(idx_a, idx_b)

        # Collect clusters by root representative
        clusters: dict[int, list[int]] = defaultdict(list)
        for idx in range(n):
            clusters[find(idx)].append(idx)

        # Sort clusters by first occurrence in input to preserve stream order
        sorted_clusters = sorted(clusters.values(), key=lambda cluster: min(cluster))

        unique_records: list[RawLeadRecord] = []
        duplicate_groups: list[DuplicateGroup] = []

        for cluster in sorted_clusters:
            if len(cluster) == 1:
                unique_records.append(leads[cluster[0]])
            else:
                # Selection rule: Highest completeness score wins;
                # on tie, earliest appearance in input wins.
                kept_idx = max(
                    cluster,
                    key=lambda idx: (self.compute_completeness_score(leads[idx]), -idx),
                )
                kept_record = leads[kept_idx]
                removed_records = [leads[idx] for idx in cluster if idx != kept_idx]

                reason_code, matched_fields = self._determine_group_evidence(
                    kept_idx=kept_idx,
                    removed_indices=[idx for idx in cluster if idx != kept_idx],
                    domain_keys=domain_keys,
                    phone_keys=phone_keys,
                )

                group = DuplicateGroup(
                    kept_record=kept_record,
                    removed_records=removed_records,
                    reason_code=reason_code,
                    matched_fields=matched_fields,
                )
                unique_records.append(kept_record)
                duplicate_groups.append(group)

        return DeduplicationResult(
            unique_records=unique_records,
            duplicate_groups=duplicate_groups,
            total_processed=n,
        )

    def _is_duplicate_pair(
        self,
        domain_a: str | None,
        domain_b: str | None,
        phone_a: str | None,
        phone_b: str | None,
    ) -> bool:
        """Evaluate if two records with the same normalized name are duplicates."""
        has_domain_conflict = (
            domain_a is not None and domain_b is not None and domain_a != domain_b
        )
        if has_domain_conflict:
            # Contradictory websites for the same company name indicates distinct entities
            return False

        web_match = (
            domain_a is not None and domain_b is not None and domain_a == domain_b
        )
        phone_match = (
            phone_a is not None and phone_b is not None and phone_a == phone_b
        )

        return web_match or phone_match

    def _determine_group_evidence(
        self,
        kept_idx: int,
        removed_indices: list[int],
        domain_keys: list[str | None],
        phone_keys: list[str | None],
    ) -> tuple[DuplicateReason | str, list[str]]:
        """Determine reason_code and matched_fields for a resolved duplicate group."""
        has_web_match = False
        has_phone_match = False

        kept_domain = domain_keys[kept_idx]
        kept_phone = phone_keys[kept_idx]

        for r_idx in removed_indices:
            r_domain = domain_keys[r_idx]
            r_phone = phone_keys[r_idx]

            if kept_domain and r_domain and kept_domain == r_domain:
                has_web_match = True
            if kept_phone and r_phone and kept_phone == r_phone:
                has_phone_match = True

        matched_fields = ["company_name"]
        if has_web_match:
            matched_fields.append("website")
        if has_phone_match:
            matched_fields.append("public_phone")

        if has_web_match and has_phone_match:
            reason = DuplicateReason.NAME_AND_WEBSITE_AND_PHONE_MATCH
        elif has_web_match:
            reason = DuplicateReason.NAME_AND_WEBSITE_MATCH
        elif has_phone_match:
            reason = DuplicateReason.NAME_AND_PHONE_MATCH
        else:
            # Transitive cluster match fallback
            reason = DuplicateReason.NAME_AND_WEBSITE_MATCH

        return reason, matched_fields

    @classmethod
    def normalize_name(cls, name: str | None) -> str:
        """Normalize company name: NFC Unicode, lowercased, and whitespace collapsed."""
        if not name or not isinstance(name, str):
            return ""
        normalized = unicodedata.normalize("NFC", name.strip()).lower()
        return re.sub(r"\s+", " ", normalized)

    @classmethod
    def normalize_website(cls, url: str | None) -> str | None:
        """Extract canonical hostname and non-default port from website URL.

        Handles:
        - Invalid URLs / syntax / disallowed schemes -> returns None
        - Uppercase hostnames -> lowercased
        - Default ports (80, 443) -> stripped; non-default ports -> preserved
        - Subdomains -> preserved distinctly (e.g. dut.udn.vn != ute.udn.vn)
        - 'www.' prefix -> stripped
        """
        if not url or not isinstance(url, str):
            return None
        cleaned = url.strip()
        if not cleaned:
            return None

        # Check for disallowed schemes early
        if ":" in cleaned:
            prefix = cleaned.split(":", 1)[0].lower()
            if prefix not in ("http", "https"):
                return None

        if "://" not in cleaned:
            cleaned = "http://" + cleaned

        try:
            parsed = urlparse(cleaned)
            netloc = parsed.netloc or ""
            if not netloc:
                return None

            # Split userinfo if present
            host_port = netloc.split("@")[-1].strip().lower()
            if not host_port:
                return None

            # Extract hostname and port
            if ":" in host_port:
                host, port_str = host_port.split(":", 1)
                try:
                    port = int(port_str)
                    if port in (80, 443):
                        port_suffix = ""
                    else:
                        port_suffix = f":{port}"
                except ValueError:
                    return None
            else:
                host = host_port
                port_suffix = ""

            if host.startswith("www."):
                host = host[4:]
            host = host.rstrip(".")

            # Validate hostname structure: must match valid domain with TLD
            if not cls._DOMAIN_REGEX.match(host):
                return None

            return f"{host}{port_suffix}"
        except Exception:
            return None

    @classmethod
    def normalize_phone(cls, phone: str | None) -> str | None:
        """Extract sanitized phone digits conforming to Vietnam telecom policy.

        Rejects arbitrary text, dummy repeated digits, and non-VN numbering plans.
        """
        if not phone or not isinstance(phone, str):
            return None
        cleaned = phone.strip()
        if not cleaned:
            return None

        # Reject strings with alphabetical letters (e.g. 'Order 1234567890')
        if re.search(r"[a-zA-Z]", cleaned):
            return None

        # Split multiple numbers by delimiter and evaluate primary number
        primary = re.split(r"[/,;]", cleaned)[0].strip()

        # Reject if contains disallowed non-phone characters
        if not re.match(r"^\+?[\d\s\.\-\(\)]+$", primary):
            return None

        # Extract digits
        digits = re.sub(r"\D", "", primary)

        # Convert international Vietnam country code (+84 or 84) to leading 0
        if primary.startswith("+84") or (digits.startswith("84") and len(digits) in (11, 12)):
            digits = "0" + digits[2:]

        # Reject dummy repeating digits (e.g. '0000000000', '0999999999', '0888888888')
        if len(set(digits)) <= 1 or (digits.startswith("0") and len(set(digits[1:])) <= 1):
            return None


        # Validate against Vietnam numbering plans
        is_mobile = bool(cls._VN_MOBILE_REGEX.match(digits))
        is_landline = bool(cls._VN_LANDLINE_REGEX.match(digits))
        is_hotline = bool(cls._VN_HOTLINE_REGEX.match(digits))

        if is_mobile or is_landline or is_hotline:
            return digits

        return None

    @classmethod
    def compute_completeness_score(cls, lead: RawLeadRecord) -> int:
        """Compute completeness score based strictly on the 11 populated canonical fields.

        Does not evaluate raw_payload or audit metadata.
        """
        score = 0
        for field_name in cls._SCORED_FIELDS:
            val = getattr(lead, field_name, None)
            if val is not None and isinstance(val, str) and val.strip():
                score += 1
        return score

