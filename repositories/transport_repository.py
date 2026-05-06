from typing import Optional, List, Dict, Any
from datetime import datetime
from datetime import date

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy import select, and_, or_, func

from fastapi import HTTPException

import logging

from models.main_models import TransportModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImportTransportDataRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.batch_size = 1000  # Process 1000 rows at a time
        self.errors = []

    async def import_transport_data(self):
        try:
            # 1. Load Excel file
            excel_path = "./static_datas/transport_data.xlsx"
            logger.info(f"Loading Excel file from {excel_path}")

            # Check if file exists
            import os
            if not os.path.exists(excel_path):
                raise Exception(f"File not found: {excel_path}")

            # Read with more debug info
            df = pd.read_excel(excel_path, dtype=str)

            logger.info(f"Total rows loaded: {len(df)}")
            logger.info(f"Columns found: {list(df.columns)}")  # ← Debug: See actual column names

            # 2. Validate and clean data
            cleaned_data, errors = await self.validate_and_clean_data(df)

            logger.info(f"Cleaned data rows: {len(cleaned_data)}")
            logger.info(f"Error rows: {len(errors)}")

            # Debug: Show first few rows of cleaned data
            if cleaned_data:
                logger.info(f"First cleaned row sample: {cleaned_data[0]}")

            if errors:
                logger.info(f"First error sample: {errors[0] if errors else 'No errors'}")

            if not cleaned_data:
                # Save errors to file for debugging
                await self.save_errors_to_file(errors)
                raise Exception(f"No valid data to import after cleaning. Total rows: {len(df)}, Errors: {len(errors)}")

            # 3. Import in batches
            await self.batch_insert(cleaned_data)

            logger.info(f"Successfully imported {len(cleaned_data)} rows")

            return {
                "total_rows": len(df),
                "successful_imports": len(cleaned_data),
                "failed_rows": len(errors),
                "errors_file": "import_errors.json" if errors else None
            }

        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            raise HTTPException(500, f"Import failed: {str(e)}")

    async def validate_and_clean_data(self, df: pd.DataFrame) -> tuple[List[Dict], List[Dict]]:
        """Validate and clean each row"""
        cleaned_data = []
        errors = []

        # Debug: Print actual columns from Excel
        print(f"Excel columns: {list(df.columns)}")

        # Define expected columns mapping (match EXACTLY with Excel)
        # Check your Excel file column names - they might be different!
        column_mapping = {
            'structure_1': 'structure_1',
            'structure_2': 'structure_2',
            'raw_labels': 'raw_labels',
            'mark_name': 'mark_name',
            't_qty': 't_qty',
            't_weight': 't_weight',
            't_date': 't_date',
            't_status': 't_status',
            'proce_qty': 'proce_qty',
            'order_no': 'order_no',
            'key': 'key',
            'area': 'area',
            'location': 'location'
        }

        # Try to find matching columns (case insensitive)
        excel_cols_lower = {col.lower().strip(): col for col in df.columns}

        for db_col, expected_excel_col in column_mapping.items():
            if expected_excel_col not in df.columns:
                # Try case insensitive match
                if expected_excel_col.lower() in excel_cols_lower:
                    actual_col = excel_cols_lower[expected_excel_col.lower()]
                    print(f"Found column '{actual_col}' for '{expected_excel_col}'")
                    column_mapping[db_col] = actual_col
                else:
                    print(f"WARNING: Column '{expected_excel_col}' not found in Excel!")
                    print(f"Available columns: {list(df.columns)}")

        # Process first few rows for debugging
        for index, row in df.head(5).iterrows():
            print(f"\nRow {index} sample:")
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                print(f"  {db_col} = '{value}'")

        for index, row in df.iterrows():
            try:
                cleaned_row = {}
                row_errors = []

                for excel_col, db_col in column_mapping.items():
                    value = row.get(excel_col)

                    # Handle each column type
                    if db_col in ['t_qty', 't_weight']:
                        cleaned_value = self.safe_float_conversion(value, db_col, index, row_errors)
                    elif db_col == 'proce_qty':
                        cleaned_value = self.safe_int_conversion(value, db_col, index, row_errors)
                    elif db_col == 't_date':
                        cleaned_value = self.safe_date_conversion(value, db_col, index, row_errors)
                    else:
                        # String fields
                        cleaned_value = self.safe_string_conversion(value)

                    cleaned_row[db_col] = cleaned_value

                # Check if row had any errors
                if row_errors:
                    errors.append({
                        "row_number": index + 2,
                        "errors": row_errors,
                        "original_data": row.to_dict()
                    })
                else:
                    cleaned_data.append(cleaned_row)

            except Exception as e:
                errors.append({
                    "row_number": index + 2,
                    "errors": [f"Unexpected error: {str(e)}"],
                    "original_data": row.to_dict()
                })

        return cleaned_data, errors

    def safe_float_conversion(self, value, field_name, row_index, errors):
        """Safely convert to float"""
        if pd.isna(value) or value == '' or value is None or str(value).lower() == 'nan':
            return None

        try:
            # Remove any currency symbols or commas
            if isinstance(value, str):
                value = value.replace(',', '').replace('$', '').replace('€', '').strip()

            float_val = float(value)
            return float_val
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid {field_name}: '{value}' - {str(e)}")
            return None

    def safe_int_conversion(self, value, field_name, row_index, errors):
        """Safely convert to integer"""
        if pd.isna(value) or value == '' or value is None or str(value).lower() == 'nan':
            return None

        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()

            int_val = int(float(value))  # Convert through float to handle decimal strings
            return int_val
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid {field_name}: '{value}' - {str(e)}")
            return None

    def safe_date_conversion(self, value, field_name, row_index, errors):
        """Safely convert to date - handles Excel serial dates"""
        if pd.isna(value) or value == '' or value is None or str(value).lower() == 'nan':
            return None

        try:
            # Check if it's an Excel serial date (number like 44342)
            if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
                # Convert Excel serial date to datetime
                excel_date = float(value)
                from datetime import datetime, timedelta
                # Excel serial date: 1 = 1900-01-01
                # Note: Excel incorrectly considers 1900 as leap year
                if excel_date > 59:  # Adjust for Excel leap year bug
                    excel_date -= 1
                base_date = datetime(1899, 12, 31)
                result_date = base_date + timedelta(days=excel_date)
                return result_date.date()

            # Try different string date formats
            if isinstance(value, str):
                value = value.strip()
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y%m%d', '%d.%m.%Y', '%m.%d.%Y']:
                    try:
                        return datetime.strptime(value, fmt).date()
                    except ValueError:
                        continue
                raise ValueError(f"Date format not recognized: {value}")
            else:
                # Try pandas conversion
                return pd.to_datetime(value).date()

        except Exception as e:
            errors.append(f"Invalid {field_name}: '{value}' - {str(e)}")
            return None

    def safe_string_conversion(self, value):
        """Safely convert to string"""
        if pd.isna(value) or value is None or str(value).lower() == 'nan':
            return None
        str_value = str(value).strip()
        return str_value[:255] if len(str_value) > 255 else str_value

    async def batch_insert(self, cleaned_data: List[Dict]):
        """Insert data in batches for better performance"""
        total_batches = (len(cleaned_data) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(cleaned_data), self.batch_size):
            batch = cleaned_data[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1

            logger.info(f"Inserting batch {batch_num}/{total_batches} ({len(batch)} rows)")

            try:
                # Build insert statement
                insert_stmt = text("""
                    INSERT INTO transports (
                        structure_1, structure_2, raw_labels, mark_name, 
                        t_qty, t_weight, t_date, t_status, proce_qty, 
                        order_no, key, area, location, created_at
                    ) VALUES (
                        :structure_1, :structure_2, :raw_labels, :mark_name,
                        :t_qty, :t_weight, :t_date, :t_status, :proce_qty,
                        :order_no, :key, :area, :location, NOW()
                    )
                """)

                # Execute batch
                for row in batch:
                    # Convert None to proper NULL for PostgreSQL
                    for key, value in row.items():
                        if value is None:
                            row[key] = None

                    await self.db.execute(insert_stmt, row)

                await self.db.commit()
                logger.info(f"Batch {batch_num} committed successfully")

            except Exception as e:
                await self.db.rollback()
                logger.error(f"Batch {batch_num} failed: {str(e)}")
                raise Exception(f"Failed to insert batch {batch_num}: {str(e)}")

    async def save_errors_to_file(self, errors: List[Dict]):
        """Save errors to JSON file for review"""
        import json
        from datetime import datetime

        error_file = f"./static_datas/import_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(error_file, 'w') as f:
            json.dump({
                "total_errors": len(errors),
                "timestamp": datetime.now().isoformat(),
                "errors": errors
            }, f, indent=2, default=str)

        logger.info(f"Errors saved to {error_file}")




class FetchTransportDataRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_transport_data(
            self,
            limit: int = 100,
            offset: int = 0,
            # Optional filters
            structure_1: Optional[str] = None,
            structure_2: Optional[str] = None,
            mark_name: Optional[str] = None,
            order_no: Optional[str] = None,
            area: Optional[str] = None,
            location: Optional[str] = None,
            t_status: Optional[str] = None,
            t_date_from: Optional[date] = None,
            t_date_to: Optional[date] = None,
            min_weight: Optional[float] = None,
            max_weight: Optional[float] = None,
            search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch transport data with pagination and filters
        """
        try:
            # Build query
            query = select(TransportModel)

            # Apply filters
            filters = []

            if structure_1:
                filters.append(TransportModel.structure_1 == structure_1)

            if structure_2:
                filters.append(TransportModel.structure_2 == structure_2)

            if mark_name:
                filters.append(TransportModel.mark_name.ilike(f"%{mark_name}%"))

            if order_no:
                filters.append(TransportModel.order_no.ilike(f"%{order_no}%"))

            if area:
                filters.append(TransportModel.area == area)

            if location:
                filters.append(TransportModel.location == location)

            if t_status:
                filters.append(TransportModel.t_status == t_status)

            if t_date_from:
                filters.append(TransportModel.t_date >= t_date_from)

            if t_date_to:
                filters.append(TransportModel.t_date <= t_date_to)

            if min_weight is not None:
                filters.append(TransportModel.t_weight >= min_weight)

            if max_weight is not None:
                filters.append(TransportModel.t_weight <= max_weight)

            if search:
                # Search across multiple text fields
                search_filter = or_(
                    TransportModel.structure_1.ilike(f"%{search}%"),
                    TransportModel.structure_2.ilike(f"%{search}%"),
                    TransportModel.raw_labels.ilike(f"%{search}%"),
                    TransportModel.mark_name.ilike(f"%{search}%"),
                    TransportModel.order_no.ilike(f"%{search}%"),
                    TransportModel.key.ilike(f"%{search}%"),
                    TransportModel.area.ilike(f"%{search}%"),
                    TransportModel.location.ilike(f"%{search}%")
                )
                filters.append(search_filter)

            if filters:
                query = query.where(and_(*filters))

            # Get total count
            count_query = select(func.count()).select_from(TransportModel)
            if filters:
                count_query = count_query.where(and_(*filters))

            total_count = await self.db.scalar(count_query)

            # Add pagination and ordering
            query = query.order_by(TransportModel.id.asc())
            query = query.offset(offset).limit(limit)

            # Execute query
            result = await self.db.execute(query)
            items = result.scalars().all()

            # Convert to list of dictionaries
            data = []
            for item in items:
                data.append({
                    "id": item.id,
                    "structure_1": item.structure_1,
                    "structure_2": item.structure_2,
                    "raw_labels": item.raw_labels,
                    "mark_name": item.mark_name,
                    "t_qty": item.t_qty,
                    "t_weight": item.t_weight,
                    "t_date": item.t_date.isoformat() if item.t_date else None,
                    "t_status": item.t_status,
                    "proce_qty": item.proce_qty,
                    "order_no": item.order_no,
                    "key": item.key,
                    "area": item.area,
                    "location": item.location,
                    "created_by": item.created_by,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                })

            return {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "items": data
            }

        except Exception as e:
            logger.error(f"Failed to fetch transport data: {str(e)}")
            raise Exception(f"Database query failed: {str(e)}")

    async def get_transport_by_id(self, transport_id: int) -> Optional[Dict]:
        """Fetch a single transport by ID"""
        try:
            query = select(TransportModel).where(TransportModel.id == transport_id)
            result = await self.db.execute(query)
            item = result.scalar_one_or_none()

            if item:
                return {
                    "id": item.id,
                    "structure_1": item.structure_1,
                    "structure_2": item.structure_2,
                    "raw_labels": item.raw_labels,
                    "mark_name": item.mark_name,
                    "t_qty": item.t_qty,
                    "t_weight": item.t_weight,
                    "t_date": item.t_date.isoformat() if item.t_date else None,
                    "t_status": item.t_status,
                    "proce_qty": item.proce_qty,
                    "order_no": item.order_no,
                    "key": item.key,
                    "area": item.area,
                    "location": item.location,
                    "created_by": item.created_by,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                }
            return None

        except Exception as e:
            logger.error(f"Failed to fetch transport by ID {transport_id}: {str(e)}")
            raise Exception(f"Database query failed: {str(e)}")

    async def get_unique_values(self, column_name: str) -> List[str]:
        """Get unique values for a specific column (for filters)"""
        try:
            column = getattr(TransportModel, column_name, None)
            if not column:
                raise ValueError(f"Invalid column name: {column_name}")

            query = select(column).where(column.isnot(None)).distinct()
            result = await self.db.execute(query)
            values = result.scalars().all()

            return sorted([v for v in values if v])

        except Exception as e:
            logger.error(f"Failed to get unique values for {column_name}: {str(e)}")
            raise Exception(f"Query failed: {str(e)}")