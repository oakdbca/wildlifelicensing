import json
import re
from decimal import Decimal

from dateutil.parser import parse as date_parse
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font
from tableschema.types import (
    cast_date,
    cast_datetime,
    cast_integer,
    cast_number,
    cast_string,
)

from wildlifelicensing.apps.main.excel import is_blank_value

COLUMN_HEADER_FONT = Font(bold=True)

YYYY_MM_DD_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}")


class FieldSchemaError(Exception):
    pass


class InvalidDateType(ValueError):
    pass


def parse_datetime_day_first(value):
    dayfirst = not YYYY_MM_DD_REGEX.match(value)
    return date_parse(value, dayfirst=dayfirst)


def cast_dayfirst_date(format, value, **options):
    try:
        if isinstance(value, str):
            return parse_datetime_day_first(value).date()
        return cast_date(format, value, **options)
    except Exception as e:
        raise InvalidDateType(e) from e


def cast_dayfirst_datetime(format, value, **options):
    try:
        if isinstance(value, str):
            return parse_datetime_day_first(value)
        return cast_datetime(format, value, **options)
    except Exception as e:
        raise InvalidDateType(e) from e


def cast_not_blank_string(format, value, **options):
    null_values = ["null", "none", "nil", "nan", "-", ""]
    if value in null_values:
        raise ValueError("Blank value not allowed")
    return cast_string(format, value, **options)


class WLSchema:
    SPECIES_TYPE_NAME = "species"
    SPECIES_TYPE_FLORA_NAME = "flora"
    SPECIES_TYPE_FAUNA_NAME = "fauna"

    def __init__(self, data):
        self.data = data or {}

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def __str__(self):
        return f"WLSchema: {self.data}"

    @property
    def type(self):
        return self.get("type")

    @property
    def species_type(self):
        return self.get("speciesType")

    def get(self, k, d=None):
        return self.data.get(k, d)

    def is_species_type(self):
        return self.type == self.SPECIES_TYPE_NAME


class SchemaField:
    # Map type names to casting functions
    BASE_TYPE_MAP = {
        "date": cast_dayfirst_date,
        "datetime": cast_dayfirst_datetime,
        "string": cast_not_blank_string,
        "integer": cast_integer,
        "number": cast_number,
    }
    WL_TYPE_MAP = {}

    def __init__(self, data):
        self.data = data
        self.name = self.data.get("name")
        if not self.name:
            raise FieldSchemaError(f"A field without a name: {json.dumps(data)}")
        self.wl = WLSchema(self.data.get("wl"))
        # wl type as precedence
        type_func = self.WL_TYPE_MAP.get(self.wl.type) or self.BASE_TYPE_MAP.get(
            self.data.get("type")
        )
        self.type_func = type_func
        self.constraints = SchemaConstraints(self.data.get("constraints", {}))

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def get(self, k, d=None):
        return self.data.get(k, d)

    @property
    def title(self):
        return self.data.get("title")

    @property
    def column_name(self):
        return self.name

    @property
    def required(self):
        return self.constraints.required

    @property
    def is_species(self):
        return self.wl.is_species_type()

    @property
    def species_type(self):
        result = None
        if self.is_species:
            return self.wl.species_type or "all"
        return result

    def cast(self, value):
        if self.type_func is None:
            raise FieldSchemaError(f"No type function for field {self.name}")

        # Skip blank values (let required constraint handle them)
        if is_blank_value(value):
            return value

        # Try to cast first
        casted = self.type_func(None, value)

        # Enforce constraints
        constraints = self.constraints
        if self.data.get("type") in ("number", "integer"):
            # Only check constraints if casted is a number
            if not isinstance(casted, (int, float, Decimal)):
                raise ValueError(f"Value {value} could not be converted to a number")
            if constraints.get("minimum") is not None and casted < constraints.get(
                "minimum"
            ):
                raise ValueError(
                    f"Value {casted} is less than minimum {constraints.get('minimum')}"
                )
            if constraints.get("maximum") is not None and casted > constraints.get(
                "maximum"
            ):
                raise ValueError(
                    f"Value {casted} is greater than maximum {constraints.get('maximum')}"
                )
        if constraints.enum is not None and casted not in constraints.enum:
            raise ValueError(f"Value {casted} is not in enum {constraints.enum}")
        return casted

    def validate(self, value):
        return self.validation_error(value)

    def validation_error(self, value):
        error = None
        # Integer validation
        if self.data.get("type") == "integer":
            if not is_blank_value(value):
                not_integer = False
                try:
                    casted = self.cast(value)
                    if str(casted) != str(value):
                        not_integer = True
                except Exception:
                    not_integer = True
                if not_integer:
                    return f'The field "{self.name}" must be a whole number.'

        # Number validation
        if self.data.get("type") == "number":
            if not is_blank_value(value):
                try:
                    casted = self.cast(value)
                except Exception as e:
                    error = f"{e}"
                    if error.find("enum array") and self.constraints.enum:
                        values = [str(v) for v in self.constraints.enum]
                        error = f"The value must be one the following: {values}"
                    elif "decimal.ConversionSyntax" in str(e):
                        error = f'The field "{self.name}" must be a number.'
                    return error

        try:
            self.cast(value)
        except Exception as e:
            error = f"{e}"
            if error.find("enum array") and self.constraints.enum:
                values = [str(v) for v in self.constraints.enum]
                error = f"The value must be one the following: {values}"
        return error

    def __str__(self):
        return f"{self.name}"


class SchemaConstraints:
    def __init__(self, data):
        self.data = data or {}

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def get(self, k, d=None):
        return self.data.get(k, d)

    @property
    def required(self):
        return self.get("required", False)

    @property
    def enum(self):
        return self.get("enum")


class Schema:
    def __init__(self, schema):
        self.data = schema
        self.fields = [SchemaField(f) for f in schema.get("fields", [])]
        self.species_fields = self.find_species_fields(self)

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def get(self, k, d=None):
        return self.data.get(k, d)

    @staticmethod
    def find_species_fields(schema):
        if not isinstance(schema, Schema):
            schema = Schema(schema)
        return [f for f in schema.fields if f.is_species]

    @property
    def headers(self):
        return self.field_names

    @property
    def field_names(self):
        return [f.name for f in self.fields]

    def get_field_by_name(self, name, icase=False):
        if icase and name:
            name = name.lower()
        for f in self.fields:
            field_name = f.name.lower() if icase else f.name
            if field_name == name:
                return f
        return None

    def field_validation_error(self, field_name, value):
        field = self.get_field_by_name(field_name)
        if field is not None:
            return field.validation_error(value)
        else:
            raise Exception(
                "The field '{}' doesn't exists in the schema. Should be one of {}".format(
                    field_name, self.field_names
                )
            )

    def is_field_valid(self, field_name, value):
        return self.field_validation_error(field_name, value) is None

    def is_lat_long_easting_northing_schema(self):
        field_names = [name.lower() for name in self.field_names]
        return all(
            [
                "latitude" in field_names,
                "longitude" in field_names,
                "easting" in field_names,
                "northing" in field_names,
                "zone" in field_names,
            ]
        )

    def post_validate_lat_long_easting_northing(self, field_validation):
        if not self.is_lat_long_easting_northing_schema():
            return field_validation
        lat_validation = field_validation.get(
            self.get_field_by_name("latitude", icase=True).name, {}
        )
        north_validation = field_validation.get(
            self.get_field_by_name("northing", icase=True).name, {}
        )
        long_validation = field_validation.get(
            self.get_field_by_name("longitude", icase=True).name, {}
        )
        east_validation = field_validation.get(
            self.get_field_by_name("easting", icase=True).name, {}
        )
        zone_validation = field_validation.get(
            self.get_field_by_name("zone", icase=True).name, {}
        )
        if lat_validation.get("value") and long_validation.get("value"):
            if not north_validation.get("value"):
                north_validation["error"] = None
                zone_validation["error"] = None
            if not east_validation.get("value"):
                east_validation["error"] = None
                zone_validation["error"] = None
        if east_validation.get("value") and north_validation.get("value"):
            if not lat_validation.get("value"):
                lat_validation["error"] = None
            if not long_validation.get("value"):
                long_validation["error"] = None
        return field_validation

    def validate_row(self, row):
        row = dict(row)
        result = {}
        for field_name, value in row.items():
            error = self.field_validation_error(field_name, value)
            result[field_name] = {"value": value, "error": error}

        # Special case for lat/long easting/northing
        if self.is_lat_long_easting_northing_schema():
            result = self.post_validate_lat_long_easting_northing(result)

            # --- ADD THIS BLOCK ---
            # Enforce: must have (latitude AND longitude) OR (zone AND easting AND northing)
            lat = row.get("LATITUDE")
            lon = row.get("LONGITUDE")
            zone = row.get("ZONE")
            easting = row.get("EASTING")
            northing = row.get("NORTHING")

            has_latlon = not is_blank_value(lat) and not is_blank_value(lon)
            has_grid = (
                not is_blank_value(zone)
                and not is_blank_value(easting)
                and not is_blank_value(northing)
            )

            if not (has_latlon or has_grid):
                msg = (
                    "You must provide either both LATITUDE and LONGITUDE, "
                    "or all of ZONE, EASTING, and NORTHING."
                )
                # Attach error to all relevant fields if missing
                for fname in ["LATITUDE", "LONGITUDE", "ZONE", "EASTING", "NORTHING"]:
                    if fname in result:
                        result[fname]["error"] = msg

        return result

    def rows_validator(self, rows):
        for row in rows:
            yield self.validate_row(row)

    def get_error_fields(self, row):
        validated_row = self.validate_row(row)
        errors = []
        for field, data in validated_row.items():
            if data.get("error"):
                errors.append((field, data))
        return errors

    def is_row_valid(self, row):
        return len(self.get_error_fields(row)) == 0

    def is_all_valid(self, rows):
        for row in rows:
            if not self.is_row_valid(row):
                return False
        return True


def create_return_template_workbook(return_type):
    wb = Workbook(write_only=True)
    for resource in return_type.resources:
        schema = Schema(resource.get("schema"))
        ws = wb.create_sheet()
        ws.title = resource.get("title", resource.get("name"))
        headers = []
        for header in schema.headers:
            cell = WriteOnlyCell(ws, value=header)
            cell.font = COLUMN_HEADER_FONT
            headers.append(cell)
        ws.append(headers)
    return wb
