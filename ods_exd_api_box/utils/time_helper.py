"""
Helper functions for time conversions and checks.
"""
import datetime

class TimeHelper:

    @staticmethod
    def to_asam_ods_time(datetime_value: any) -> str:
        """Convert datetime value to ASAM ODS time format YYYYMMDDhhmmss[fffffffff] (nanoseconds).

        Trailing zeros in fractional seconds are removed.

        Supports:
        - numpy datetime64 (without importing numpy)
        - Unix timestamps (int/float seconds since epoch)
        - Python datetime.datetime and datetime.date objects

        Args:
            datetime_value: Value to convert

        Returns:
            String in format YYYYMMDDhhmmss or YYYYMMDDhhmmssN (without trailing zeros)

        Raises:
            ValueError: If value cannot be converted
        """
        try:
            # Handle numpy datetime64 (check type name to avoid numpy import)
            if hasattr(datetime_value, 'dtype'):
                dtype_str = str(datetime_value.dtype)
                if 'datetime64' in dtype_str:
                    # Convert numpy datetime64 to ISO string, then parse
                    iso_str = str(datetime_value)
                    # Parse format like "2023-01-15T10:30:45.123456789"
                    dt = datetime.datetime.fromisoformat(iso_str.replace('T', 'T'))
                    # Extract nanoseconds from fractional seconds
                    if '.' in iso_str:
                        frac_str = iso_str.split('.')[1][:9].ljust(9, '0')
                    else:
                        frac_str = '000000000'
                    return dt.strftime('%Y%m%d%H%M%S') + frac_str.rstrip('0')

            # Handle Python datetime objects
            if isinstance(datetime_value, datetime.datetime):
                ns = datetime_value.microsecond * 1000  # Convert microseconds to nanoseconds
                frac_str = f'{ns:09d}'.rstrip('0')
                return datetime_value.strftime('%Y%m%d%H%M%S') + frac_str

            if isinstance(datetime_value, datetime.date):
                return datetime_value.strftime('%Y%m%d') + '000000'

            # Handle Unix timestamps (float or int seconds since epoch)
            if isinstance(datetime_value, (int, float)):
                dt = datetime.datetime.fromtimestamp(datetime_value, tz=datetime.timezone.utc)
                # Extract fractional seconds as nanoseconds
                ns = int((datetime_value % 1) * 1e9)
                frac_str = f'{ns:09d}'.rstrip('0')
                return dt.strftime('%Y%m%d%H%M%S') + frac_str

        except Exception as e:
            raise ValueError(f"Unable to convert {datetime_value} to ASAM ODS time format: {e}")

        raise ValueError(f"Unsupported datetime type: {type(datetime_value)}")

    @staticmethod
    def is_datetime_type(value: any) -> bool:
        """Check if value is a datetime type without importing numpy."""
        # Python datetime types
        if isinstance(value, (datetime.datetime, datetime.date)):
            return True

        # Unix timestamp (numeric)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return False  # Would be handled as int/float

        # numpy datetime64 (check type name to avoid import)
        if hasattr(value, 'dtype'):
            return 'datetime64' in str(value.dtype)

        return False