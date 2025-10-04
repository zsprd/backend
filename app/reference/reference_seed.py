"""
Reference Data Seeding Script

Fetches country, currency, language, and timezone data from REST Countries API
and populates the reference tables in the database.

Usage:
    python -m app.scripts.seed_reference_data

    Or from within the app:
    from app.scripts.seed_reference_data import seed_all_reference_data
    await seed_all_reference_data()
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.reference.countries.model import ReferenceCountry
from app.reference.currencies.model import ReferenceCurrency
from app.reference.languages.model import ReferenceLanguage
from app.reference.timezones.model import ReferenceTimezone

logger = logging.getLogger(__name__)

# REST Countries API Configuration
RESTCOUNTRIES_API_BASE = "https://restcountries.com/v3.1"
RESTCOUNTRIES_TIMEOUT = 30.0


class ReferenceDataSeeder:
    """Handles fetching and seeding reference data from REST Countries API."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.stats = {
            "countries_added": 0,
            "countries_updated": 0,
            "currencies_added": 0,
            "currencies_updated": 0,
            "languages_added": 0,
            "languages_updated": 0,
            "timezones_added": 0,
            "timezones_updated": 0,
            "errors": [],
        }

    async def fetch_countries_data(self) -> Optional[List[Dict]]:
        """
        Fetch all countries data from REST Countries API.

        Note: API requires field specification (max 10 fields per request).
        We make 2 calls and merge the data.
        """
        url = f"{RESTCOUNTRIES_API_BASE}/all"

        try:
            async with httpx.AsyncClient(timeout=RESTCOUNTRIES_TIMEOUT) as client:
                # First call: Core identification and reference data (10 fields)
                logger.info(f"Fetching core country data from REST Countries API...")
                fields_1 = (
                    "name,cca2,cca3,capital,region,currencies,languages,timezones,flags,population"
                )
                response_1 = await client.get(url, params={"fields": fields_1})
                response_1.raise_for_status()
                data_1 = response_1.json()
                logger.info(f"Successfully fetched core data for {len(data_1)} countries")

                # Second call: Additional geographic and political data (7 fields)
                logger.info(f"Fetching additional country data...")
                fields_2 = "cca2,subregion,continents,latlng,area,independent,unMember"
                response_2 = await client.get(url, params={"fields": fields_2})
                response_2.raise_for_status()
                data_2 = response_2.json()
                logger.info(f"Successfully fetched additional data for {len(data_2)} countries")

                # Merge data by cca2 code
                logger.info("Merging country data...")
                merged_data = {}

                # Index first dataset by cca2
                for country in data_1:
                    cca2 = country.get("cca2")
                    if cca2:
                        merged_data[cca2] = country

                # Merge second dataset
                for country in data_2:
                    cca2 = country.get("cca2")
                    if cca2 and cca2 in merged_data:
                        merged_data[cca2].update(country)

                result = list(merged_data.values())
                logger.info(f"Successfully merged data for {len(result)} countries")
                return result

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching countries data: {e}")
            self.stats["errors"].append(f"API fetch error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching countries data: {e}")
            self.stats["errors"].append(f"Unexpected error: {str(e)}")
            return None

    def extract_currencies(self, countries_data: List[Dict]) -> Dict[str, Dict]:
        """Extract unique currencies from countries data."""
        currencies = {}

        for country in countries_data:
            country_currencies = country.get("currencies", {})
            for code, info in country_currencies.items():
                if code not in currencies:
                    currencies[code] = {
                        "code": code,
                        "name": info.get("name", code),
                        "symbol": info.get("symbol"),
                    }

        logger.info(f"Extracted {len(currencies)} unique currencies")
        return currencies

    def extract_languages(self, countries_data: List[Dict]) -> Dict[str, Dict]:
        """Extract unique languages from countries data."""
        languages = {}

        for country in countries_data:
            country_languages = country.get("languages", {})
            for code, name in country_languages.items():
                if code not in languages:
                    # REST Countries uses ISO 639-3 codes (3-letter)
                    # We'll store them and try to map to ISO 639-1 (2-letter) where possible
                    languages[code] = {
                        "code_iso3": code,
                        "name": name,
                    }

        logger.info(f"Extracted {len(languages)} unique languages")
        return languages

    def extract_timezones(self, countries_data: List[Dict]) -> Dict[str, Dict]:
        """Extract unique timezones from countries data."""
        timezones = {}

        for country in countries_data:
            country_timezones = country.get("timezones", [])
            for tz in country_timezones:
                if tz not in timezones:
                    # Parse UTC offset from format like "UTC-05:00" or "UTC+09:00"
                    offset_str = tz.replace("UTC", "").strip()
                    if offset_str:
                        try:
                            # Convert to minutes
                            sign = 1 if offset_str[0] == "+" else -1
                            time_parts = offset_str.lstrip("+-").split(":")
                            hours = int(time_parts[0])
                            minutes = int(time_parts[1]) if len(time_parts) > 1 else 0
                            offset_minutes = sign * (hours * 60 + minutes)
                        except (ValueError, IndexError):
                            offset_minutes = 0
                    else:
                        offset_minutes = 0

                    timezones[tz] = {
                        "name": tz,
                        "utc_offset": offset_str if offset_str else "UTC+00:00",
                        "utc_offset_minutes": offset_minutes,
                    }

        logger.info(f"Extracted {len(timezones)} unique timezones")
        return timezones

    async def seed_currencies(self, currencies: Dict[str, Dict]) -> None:
        """Seed or update currencies in the database."""
        logger.info("Seeding currencies...")

        for code, info in currencies.items():
            try:
                # Check if currency exists
                stmt = select(ReferenceCurrency).where(ReferenceCurrency.currency_code == code)
                result = await self.session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.name = info["name"]
                    existing.symbol = info.get("symbol")
                    self.stats["currencies_updated"] += 1
                else:
                    # Create new
                    currency = ReferenceCurrency(
                        currency_code=code,
                        currency_name=info["name"],
                        symbol=info.get("symbol"),
                        decimal_places=0 if code in ["JPY", "KRW", "VND"] else 2,
                        is_active=True,
                    )
                    self.session.add(currency)
                    self.stats["currencies_added"] += 1

            except Exception as e:
                logger.error(f"Error seeding currency {code}: {e}")
                self.stats["errors"].append(f"Currency {code}: {str(e)}")

        await self.session.flush()
        logger.info(
            f"Currencies seeded: {self.stats['currencies_added']} added, "
            f"{self.stats['currencies_updated']} updated"
        )

    async def seed_languages(self, languages: Dict[str, Dict]) -> None:
        """Seed or update languages in the database."""
        logger.info("Seeding languages...")

        # Mapping of ISO 639-3 to ISO 639-1 for common languages
        iso3_to_iso1 = {
            "eng": "en",
            "spa": "es",
            "fra": "fr",
            "deu": "de",
            "ita": "it",
            "por": "pt",
            "rus": "ru",
            "jpn": "ja",
            "kor": "ko",
            "zho": "zh",
            "ara": "ar",
            "hin": "hi",
            "tur": "tr",
            "pol": "pl",
            "nld": "nl",
            "swe": "sv",
            "dan": "da",
            "nor": "no",
            "fin": "fi",
        }

        for code_iso3, info in languages.items():
            try:
                # Try to get ISO 639-1 code
                code_iso1 = iso3_to_iso1.get(code_iso3.lower())

                if not code_iso1:
                    # Skip languages we don't have ISO 639-1 codes for
                    continue

                # Check if language exists
                stmt = select(ReferenceLanguage).where(ReferenceLanguage.language_code == code_iso1)
                result = await self.session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.language_name = info["name"]
                    existing.language_code_iso3 = code_iso3
                    self.stats["languages_updated"] += 1
                else:
                    # Create new
                    language = ReferenceLanguage(
                        language_code=code_iso1,
                        language_code_iso3=code_iso3,
                        language_name=info["name"],
                        native_name=info["name"],
                        is_active=True,
                    )
                    self.session.add(language)
                    self.stats["languages_added"] += 1

            except Exception as e:
                logger.error(f"Error seeding language {code_iso3}: {e}")
                self.stats["errors"].append(f"Language {code_iso3}: {str(e)}")

        await self.session.flush()
        logger.info(
            f"Languages seeded: {self.stats['languages_added']} added, "
            f"{self.stats['languages_updated']} updated"
        )

    async def seed_timezones(self, timezones: Dict[str, Dict]) -> None:
        """Seed or update timezones in the database."""
        logger.info("Seeding timezones...")

        for name, info in timezones.items():
            try:
                # Check if timezone exists
                stmt = select(ReferenceTimezone).where(ReferenceTimezone.timezone_name == name)
                result = await self.session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.utc_offset = info["utc_offset"]
                    existing.utc_offset_minutes = info["utc_offset_minutes"]
                    self.stats["timezones_updated"] += 1
                else:
                    # Create new
                    timezone = ReferenceTimezone(
                        timezone_name=name,
                        utc_offset=info["utc_offset"],
                        utc_offset_minutes=info["utc_offset_minutes"],
                        is_active=True,
                    )
                    self.session.add(timezone)
                    self.stats["timezones_added"] += 1

            except Exception as e:
                logger.error(f"Error seeding timezone {name}: {e}")
                self.stats["errors"].append(f"Timezone {name}: {str(e)}")

        await self.session.flush()
        logger.info(
            f"Timezones seeded: {self.stats['timezones_added']} added, "
            f"{self.stats['timezones_updated']} updated"
        )

    async def seed_countries(self, countries_data: List[Dict]) -> None:
        """Seed or update countries in the database."""
        logger.info("Seeding countries...")

        for country_data in countries_data:
            try:
                cca2 = country_data.get("cca2")
                if not cca2:
                    continue

                # Check if country exists
                stmt = select(ReferenceCountry).where(ReferenceCountry.country_code == cca2)
                result = await self.session.execute(stmt)
                existing = result.scalar_one_or_none()

                # Extract data
                name_data = country_data.get("name", {})
                common_name = name_data.get("common", cca2)
                official_name = name_data.get("official")

                # Get primary currency
                currencies = country_data.get("currencies", {})
                primary_currency = list(currencies.keys())[0] if currencies else None

                # Get coordinates
                latlng = country_data.get("latlng", [])
                latitude = latlng[0] if len(latlng) > 0 else None
                longitude = latlng[1] if len(latlng) > 1 else None

                # Get continent (first one if multiple)
                continents = country_data.get("continents", [])
                continent = continents[0] if continents else None

                # Get capital (first one if multiple)
                capitals = country_data.get("capital", [])
                capital = capitals[0] if capitals else None

                # Determine if developed market (simplified classification)
                developed_regions = {"Europe", "Northern America", "Australia and New Zealand"}
                region = country_data.get("region", "")
                subregion = country_data.get("subregion", "")
                is_developed = region in developed_regions or subregion in developed_regions

                # Get flags
                flags = country_data.get("flags", {})
                flag_emoji = flags.get("emoji") if isinstance(flags, dict) else None
                # Fallback to flag field if emoji not present
                if not flag_emoji and "flag" in country_data:
                    flag_emoji = country_data.get("flag")

                country_dict = {
                    "country_code": cca2,
                    "country_code_alpha3": country_data.get("cca3"),
                    "country_name": common_name,
                    "official_name": official_name,
                    "capital": capital,
                    "region": region,
                    "subregion": subregion,
                    "continent": continent,
                    "latitude": latitude,
                    "longitude": longitude,
                    "currency_code": primary_currency,
                    "is_developed": is_developed,
                    "population": country_data.get("population"),
                    "area": country_data.get("area"),
                    "independent": country_data.get("independent"),
                    "un_member": country_data.get("unMember"),
                    "flag_emoji": flag_emoji,
                    "flag_svg_url": flags.get("svg") if isinstance(flags, dict) else None,
                    "is_active": True,
                }

                if existing:
                    # Update existing
                    for key, value in country_dict.items():
                        if key != "country_code":  # Don't update primary key
                            setattr(existing, key, value)
                    self.stats["countries_updated"] += 1
                else:
                    # Create new
                    country = ReferenceCountry(**country_dict)
                    self.session.add(country)
                    self.stats["countries_added"] += 1

            except Exception as e:
                logger.error(f"Error seeding country {country_data.get('cca2', 'UNKNOWN')}: {e}")
                self.stats["errors"].append(
                    f"Country {country_data.get('cca2', 'UNKNOWN')}: {str(e)}"
                )

        await self.session.flush()
        logger.info(
            f"Countries seeded: {self.stats['countries_added']} added, "
            f"{self.stats['countries_updated']} updated"
        )

    async def seed_all(self) -> Dict:
        """Main method to seed all reference data."""
        logger.info("=" * 60)
        logger.info("Starting reference data seeding from REST Countries API")
        logger.info("=" * 60)

        start_time = datetime.now(timezone.utc)

        try:
            # Fetch countries data
            countries_data = await self.fetch_countries_data()
            if not countries_data:
                logger.error("Failed to fetch countries data, aborting")
                return self.stats

            # Extract reference data
            currencies = self.extract_currencies(countries_data)
            languages = self.extract_languages(countries_data)
            timezones = self.extract_timezones(countries_data)

            # Seed in order (currencies and languages first, as countries reference them)
            await self.seed_currencies(currencies)
            await self.seed_languages(languages)
            await self.seed_timezones(timezones)
            await self.seed_countries(countries_data)

            # Commit all changes
            await self.session.commit()
            logger.info("All reference data committed successfully")

        except Exception as e:
            logger.error(f"Error during seeding process: {e}")
            await self.session.rollback()
            self.stats["errors"].append(f"Seeding process error: {str(e)}")

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 60)
        logger.info("Reference data seeding completed")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(
            f"Countries: {self.stats['countries_added']} added, {self.stats['countries_updated']} updated"
        )
        logger.info(
            f"Currencies: {self.stats['currencies_added']} added, {self.stats['currencies_updated']} updated"
        )
        logger.info(
            f"Languages: {self.stats['languages_added']} added, {self.stats['languages_updated']} updated"
        )
        logger.info(
            f"Timezones: {self.stats['timezones_added']} added, {self.stats['timezones_updated']} updated"
        )
        logger.info(f"Errors: {len(self.stats['errors'])}")
        logger.info("=" * 60)

        return self.stats


async def seed_all_reference_data() -> Dict:
    """
    Main entry point for seeding all reference data.

    Returns:
        Dict with seeding statistics
    """
    async with AsyncSessionLocal() as session:
        seeder = ReferenceDataSeeder(session)
        return await seeder.seed_all()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run seeding
    asyncio.run(seed_all_reference_data())
