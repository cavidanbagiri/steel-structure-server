import logging
import pandas as pd

from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy import select, and_, or_, func

from models.main_models import TransportModel, Combine, Mains, Erected

from schemas.transport_schema import InsertErectedSchema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#
# class ImportTransportDataRepository:
#     def __init__(self, db: AsyncSession):
#         self.db = db
#         self.batch_size = 1000  # Process 1000 rows at a time
#         self.errors = []
#
#     async def import_transport_data(self):
#         try:
#             # 1. Load Excel file
#             excel_path = "./static_datas/transport_data.xlsx"
#             logger.info(f"Loading Excel file from {excel_path}")
#
#             # Check if file exists
#             import os
#             if not os.path.exists(excel_path):
#                 raise Exception(f"File not found: {excel_path}")
#
#             # Read with more debug info
#             df = pd.read_excel(excel_path, dtype=str)
#
#             logger.info(f"Total rows loaded: {len(df)}")
#             logger.info(f"Columns found: {list(df.columns)}")  # ← Debug: See actual column names
#
#             # 2. Validate and clean data
#             cleaned_data, errors = await self.validate_and_clean_data(df)
#
#             logger.info(f"Cleaned data rows: {len(cleaned_data)}")
#             logger.info(f"Error rows: {len(errors)}")
#
#             # Debug: Show first few rows of cleaned data
#             if cleaned_data:
#                 logger.info(f"First cleaned row sample: {cleaned_data[0]}")
#
#             if errors:
#                 logger.info(f"First error sample: {errors[0] if errors else 'No errors'}")
#
#             if not cleaned_data:
#                 # Save errors to file for debugging
#                 await self.save_errors_to_file(errors)
#                 raise Exception(f"No valid data to import after cleaning. Total rows: {len(df)}, Errors: {len(errors)}")
#
#             # 3. Import in batches
#             await self.batch_insert(cleaned_data)
#
#             logger.info(f"Successfully imported {len(cleaned_data)} rows")
#
#             return {
#                 "total_rows": len(df),
#                 "successful_imports": len(cleaned_data),
#                 "failed_rows": len(errors),
#                 "errors_file": "import_errors.json" if errors else None
#             }
#
#         except Exception as e:
#             logger.error(f"Import failed: {str(e)}")
#             raise HTTPException(500, f"Import failed: {str(e)}")
#
#     async def validate_and_clean_data(self, df: pd.DataFrame) -> tuple[List[Dict], List[Dict]]:
#         """Validate and clean each row"""
#         cleaned_data = []
#         errors = []
#
#         # Debug: Print actual columns from Excel
#         print(f"Excel columns: {list(df.columns)}")
#
#         # Define expected columns mapping (match EXACTLY with Excel)
#         # Check your Excel file column names - they might be different!
#         column_mapping = {
#             'structure_1': 'structure_1',
#             'structure_2': 'structure_2',
#             'raw_labels': 'raw_labels',
#             'mark_name': 'mark_name',
#             't_qty': 't_qty',
#             't_weight': 't_weight',
#             't_date': 't_date',
#             't_status': 't_status',
#             'proce_qty': 'proce_qty',
#             'order_no': 'order_no',
#             'key': 'key',
#             'area': 'area',
#             'location': 'location'
#         }
#
#         # Try to find matching columns (case insensitive)
#         excel_cols_lower = {col.lower().strip(): col for col in df.columns}
#
#         for db_col, expected_excel_col in column_mapping.items():
#             if expected_excel_col not in df.columns:
#                 # Try case insensitive match
#                 if expected_excel_col.lower() in excel_cols_lower:
#                     actual_col = excel_cols_lower[expected_excel_col.lower()]
#                     print(f"Found column '{actual_col}' for '{expected_excel_col}'")
#                     column_mapping[db_col] = actual_col
#                 else:
#                     print(f"WARNING: Column '{expected_excel_col}' not found in Excel!")
#                     print(f"Available columns: {list(df.columns)}")
#
#         # Process first few rows for debugging
#         for index, row in df.head(5).iterrows():
#             print(f"\nRow {index} sample:")
#             for excel_col, db_col in column_mapping.items():
#                 value = row.get(excel_col)
#                 print(f"  {db_col} = '{value}'")
#
#         for index, row in df.iterrows():
#             try:
#                 cleaned_row = {}
#                 row_errors = []
#
#                 for excel_col, db_col in column_mapping.items():
#                     value = row.get(excel_col)
#
#                     # Handle each column type
#                     if db_col in ['t_qty', 't_weight']:
#                         cleaned_value = self.safe_float_conversion(value, db_col, index, row_errors)
#                     elif db_col == 'proce_qty':
#                         cleaned_value = self.safe_int_conversion(value, db_col, index, row_errors)
#                     elif db_col == 't_date':
#                         cleaned_value = self.safe_date_conversion(value, db_col, index, row_errors)
#                     else:
#                         # String fields
#                         cleaned_value = self.safe_string_conversion(value)
#
#                     cleaned_row[db_col] = cleaned_value
#
#                 # Check if row had any errors
#                 if row_errors:
#                     errors.append({
#                         "row_number": index + 2,
#                         "errors": row_errors,
#                         "original_data": row.to_dict()
#                     })
#                 else:
#                     cleaned_data.append(cleaned_row)
#
#             except Exception as e:
#                 errors.append({
#                     "row_number": index + 2,
#                     "errors": [f"Unexpected error: {str(e)}"],
#                     "original_data": row.to_dict()
#                 })
#
#         return cleaned_data, errors
#
#     def safe_float_conversion(self, value, field_name, row_index, errors):
#         """Safely convert to float"""
#         if pd.isna(value) or value == '' or value is None or str(value).lower() == 'nan':
#             return None
#
#         try:
#             # Remove any currency symbols or commas
#             if isinstance(value, str):
#                 value = value.replace(',', '').replace('$', '').replace('€', '').strip()
#
#             float_val = float(value)
#             return float_val
#         except (ValueError, TypeError) as e:
#             errors.append(f"Invalid {field_name}: '{value}' - {str(e)}")
#             return None
#
#     def safe_int_conversion(self, value, field_name, row_index, errors):
#         """Safely convert to integer"""
#         if pd.isna(value) or value == '' or value is None or str(value).lower() == 'nan':
#             return None
#
#         try:
#             if isinstance(value, str):
#                 value = value.replace(',', '').strip()
#
#             int_val = int(float(value))  # Convert through float to handle decimal strings
#             return int_val
#         except (ValueError, TypeError) as e:
#             errors.append(f"Invalid {field_name}: '{value}' - {str(e)}")
#             return None
#
#     def safe_date_conversion(self, value, field_name, row_index, errors):
#         """Safely convert to date - handles Excel serial dates"""
#         if pd.isna(value) or value == '' or value is None or str(value).lower() == 'nan':
#             return None
#
#         try:
#             # Check if it's an Excel serial date (number like 44342)
#             if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
#                 # Convert Excel serial date to datetime
#                 excel_date = float(value)
#                 from datetime import datetime, timedelta
#                 # Excel serial date: 1 = 1900-01-01
#                 # Note: Excel incorrectly considers 1900 as leap year
#                 if excel_date > 59:  # Adjust for Excel leap year bug
#                     excel_date -= 1
#                 base_date = datetime(1899, 12, 31)
#                 result_date = base_date + timedelta(days=excel_date)
#                 return result_date.date()
#
#             # Try different string date formats
#             if isinstance(value, str):
#                 value = value.strip()
#                 for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y%m%d', '%d.%m.%Y', '%m.%d.%Y']:
#                     try:
#                         return datetime.strptime(value, fmt).date()
#                     except ValueError:
#                         continue
#                 raise ValueError(f"Date format not recognized: {value}")
#             else:
#                 # Try pandas conversion
#                 return pd.to_datetime(value).date()
#
#         except Exception as e:
#             errors.append(f"Invalid {field_name}: '{value}' - {str(e)}")
#             return None
#
#     def safe_string_conversion(self, value):
#         """Safely convert to string"""
#         if pd.isna(value) or value is None or str(value).lower() == 'nan':
#             return None
#         str_value = str(value).strip()
#         return str_value[:255] if len(str_value) > 255 else str_value
#
#     async def batch_insert(self, cleaned_data: List[Dict]):
#         """Insert data in batches for better performance"""
#         total_batches = (len(cleaned_data) + self.batch_size - 1) // self.batch_size
#
#         for i in range(0, len(cleaned_data), self.batch_size):
#             batch = cleaned_data[i:i + self.batch_size]
#             batch_num = i // self.batch_size + 1
#
#             logger.info(f"Inserting batch {batch_num}/{total_batches} ({len(batch)} rows)")
#
#             try:
#                 # Build insert statement
#                 insert_stmt = text("""
#                     INSERT INTO transports (
#                         structure_1, structure_2, raw_labels, mark_name,
#                         t_qty, t_weight, t_date, t_status, proce_qty,
#                         order_no, key, area, location, created_at
#                     ) VALUES (
#                         :structure_1, :structure_2, :raw_labels, :mark_name,
#                         :t_qty, :t_weight, :t_date, :t_status, :proce_qty,
#                         :order_no, :key, :area, :location, NOW()
#                     )
#                 """)
#
#                 # Execute batch
#                 for row in batch:
#                     # Convert None to proper NULL for PostgreSQL
#                     for key, value in row.items():
#                         if value is None:
#                             row[key] = None
#
#                     await self.db.execute(insert_stmt, row)
#
#                 await self.db.commit()
#                 logger.info(f"Batch {batch_num} committed successfully")
#
#             except Exception as e:
#                 await self.db.rollback()
#                 logger.error(f"Batch {batch_num} failed: {str(e)}")
#                 raise Exception(f"Failed to insert batch {batch_num}: {str(e)}")
#
#     async def save_errors_to_file(self, errors: List[Dict]):
#         """Save errors to JSON file for review"""
#         import json
#         from datetime import datetime
#
#         error_file = f"./static_datas/import_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
#
#         with open(error_file, 'w') as f:
#             json.dump({
#                 "total_errors": len(errors),
#                 "timestamp": datetime.now().isoformat(),
#                 "errors": errors
#             }, f, indent=2, default=str)
#
#         logger.info(f"Errors saved to {error_file}")


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
            raw_labels: Optional[str] = None,
            mark_name: Optional[str] = None,
            order_no: Optional[str] = None,
            area: Optional[str] = None,
            location: Optional[str] = None,
            key: Optional[str] = None,
            t_status: Optional[str] = None,
            t_date_from: Optional[date] = None,
            t_date_to: Optional[date] = None,
            t_qty: Optional[float] = None,
            t_weight: Optional[float] = None,
            t_leftover_qty: Optional[float] = None,
            proce_qty: Optional[float] = None,
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
                filters.append(TransportModel.structure_1.ilike(f"%{structure_1}%"))

            if structure_2:
                filters.append(TransportModel.structure_2.ilike(f"%{structure_2}%"))

            if raw_labels:
                filters.append(TransportModel.raw_labels.ilike(f"%{raw_labels}%"))

            if mark_name:
                filters.append(TransportModel.mark_name.ilike(f"%{mark_name}%"))

            if order_no:
                filters.append(TransportModel.order_no.ilike(f"%{order_no}%"))

            if area:
                filters.append(TransportModel.area.ilike(f"%{area}%"))

            if location:
                filters.append(TransportModel.location.ilike(f"%{location}%"))

            if key:
                filters.append(TransportModel.key.ilike(f"%{key}%"))

            if t_status:
                filters.append(TransportModel.t_status.ilike(f"%{t_status}%"))

            if t_date_from:
                filters.append(TransportModel.t_date >= t_date_from)

            if t_date_to:
                filters.append(TransportModel.t_date <= t_date_to)

            if t_qty is not None:
                filters.append(TransportModel.t_qty == t_qty)

            if t_weight is not None:
                filters.append(TransportModel.t_weight == t_weight)

            if t_leftover_qty is not None:
                filters.append(TransportModel.t_leftover_qty == t_leftover_qty)

            if proce_qty is not None:
                filters.append(TransportModel.proce_qty == proce_qty)

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
                    "t_leftover_qty": item.t_leftover_qty,
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

        async def get_unique_values(self, column_name: str):
            """Get unique values with statistics"""

            try:
                column = getattr(TransportModel, column_name, None)

                if column is None:
                    raise ValueError(f"Invalid column name: {column_name}")

                query = (
                    select(
                        column.label("value"),
                        func.count(TransportModel.id).label("count"),
                        func.coalesce(
                            func.sum(TransportModel.weight_total),
                            0
                        ).label("weight_total")
                    )
                    .where(column.isnot(None))
                    .group_by(column)
                    .order_by(column.asc())
                )

                result = await self.db.execute(query)

                rows = result.all()

                values = [
                    {
                        "value": row.value,
                        "count": row.count,
                        "weight_total": float(row.weight_total or 0)
                    }
                    for row in rows
                    if row.value
                ]

                return values

            except Exception as e:
                logger.error(
                    f"Failed to get unique values for {column_name}: {str(e)}"
                )

                raise Exception(f"Query failed: {str(e)}")



    #
    # async def get_unique_values(self, column_name: str) -> List[str]:
    #     """Get unique values for a specific column (for filters)"""
    #     try:
    #         column = getattr(TransportModel, column_name, None)
    #         if not column:
    #             raise ValueError(f"Invalid column name: {column_name}")
    #
    #         query = select(column).where(column.isnot(None)).distinct()
    #         result = await self.db.execute(query)
    #         values = result.scalars().all()
    #
    #         return sorted([v for v in values if v])
    #
    #     except Exception as e:
    #         logger.error(f"Failed to get unique values for {column_name}: {str(e)}")
    #         raise Exception(f"Query failed: {str(e)}")


class TransportWriteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_transport(self, data: Dict) -> Dict:
        """Insert a new transport record"""
        try:
            # Convert date string to date object if present
            if 't_date' in data and data['t_date']:
                if isinstance(data['t_date'], str):
                    data['t_date'] = datetime.strptime(data['t_date'], '%Y-%m-%d').date()

            # Create new transport instance
            new_transport = TransportModel(**data)
            self.db.add(new_transport)
            await self.db.commit()
            await self.db.refresh(new_transport)

            # Return the created record
            return {
                "id": new_transport.id,
                "structure_1": new_transport.structure_1,
                "structure_2": new_transport.structure_2,
                "raw_labels": new_transport.raw_labels,
                "mark_name": new_transport.mark_name,
                "t_qty": new_transport.t_qty,
                "t_weight": new_transport.t_weight,
                "t_date": new_transport.t_date.isoformat() if new_transport.t_date else None,
                "t_status": new_transport.t_status,
                "proce_qty": new_transport.proce_qty,
                "order_no": new_transport.order_no,
                "key": new_transport.key,
                "area": new_transport.area,
                "location": new_transport.location,
                "created_by": new_transport.created_by,
                "created_at": new_transport.created_at.isoformat() if new_transport.created_at else None,
                "updated_at": new_transport.updated_at.isoformat() if new_transport.updated_at else None
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create transport: {str(e)}")
            raise Exception(f"Create failed: {str(e)}")

    async def update_transport(self, transport_id: int, data: Dict) -> Dict:
        """Update an existing transport record"""
        try:
            # Find existing record
            query = select(TransportModel).where(TransportModel.id == transport_id)
            result = await self.db.execute(query)
            transport = result.scalar_one_or_none()

            if not transport:
                raise Exception(f"Transport with ID {transport_id} not found")

            # Update fields
            for key, value in data.items():
                if key == 't_date' and value:
                    if isinstance(value, str):
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                if hasattr(transport, key) and value is not None:
                    setattr(transport, key, value)

            await self.db.commit()
            await self.db.refresh(transport)

            # Return updated record
            return {
                "id": transport.id,
                "structure_1": transport.structure_1,
                "structure_2": transport.structure_2,
                "raw_labels": transport.raw_labels,
                "mark_name": transport.mark_name,
                "t_qty": transport.t_qty,
                "t_weight": transport.t_weight,
                "t_date": transport.t_date.isoformat() if transport.t_date else None,
                "t_status": transport.t_status,
                "proce_qty": transport.proce_qty,
                "order_no": transport.order_no,
                "key": transport.key,
                "area": transport.area,
                "location": transport.location,
                "created_by": transport.created_by,
                "created_at": transport.created_at.isoformat() if transport.created_at else None,
                "updated_at": transport.updated_at.isoformat() if transport.updated_at else None
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update transport {transport_id}: {str(e)}")
            raise Exception(f"Update failed: {str(e)}")

    async def delete_transport(self, transport_id: int) -> bool:
        """Delete a transport record"""
        try:
            query = select(TransportModel).where(TransportModel.id == transport_id)
            result = await self.db.execute(query)
            transport = result.scalar_one_or_none()

            if not transport:
                raise Exception(f"Transport with ID {transport_id} not found")

            await self.db.delete(transport)
            await self.db.commit()
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete transport {transport_id}: {str(e)}")
            raise Exception(f"Delete failed: {str(e)}")


class GetTransportByIdRepository:
    def __init__(self, db: AsyncSession, id: int):
        self.db = db
        self.id = id

    async def get_transport_by_id(self):
        try:
            query = select(TransportModel).where(TransportModel.id == self.id)
            result = await self.db.execute(query)
            item = result.scalar_one_or_none()

            if not item:
                raise HTTPException(status_code=404, detail=f"Transport with id {self.id} not found")

            return {
                "success": True,
                "data": {
                    "id": item.id,
                    "structure_1": item.structure_1,
                    "structure_2": item.structure_2,
                    "raw_labels": item.raw_labels,
                    "mark_name": item.mark_name,
                    "t_qty": item.t_qty,
                    "t_leftover_qty": item.t_leftover_qty,
                    "t_weight": item.t_weight,
                    "t_date": str(item.t_date) if item.t_date else None,
                    "t_status": item.t_status,
                    "proce_qty": item.proce_qty,
                    "order_no": item.order_no,
                    "key": item.key,
                    "area": item.area,
                    "location": item.location,
                    "created_by": item.created_by,
                    "created_at": str(item.created_at) if item.created_at else None,
                    "updated_at": str(item.updated_at) if item.updated_at else None,
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            raise Exception(f"Failed to fetch transport by id: {str(e)}")


class InsertToErectedRepository:
    def __init__(self, db: AsyncSession, insert_data: InsertErectedSchema):
        self.db = db
        self.insert_data = insert_data

    async def insert_to_erected(self):
        try:
            # 1. Get transport record
            transport_query = select(TransportModel).where(
                TransportModel.id == self.insert_data.transport_id
            )
            transport_result = await self.db.execute(transport_query)
            transport_row = transport_result.scalar_one_or_none()

            if not transport_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Transport record with id {self.insert_data.transport_id} not found"
                )

            # 2. Validate against t_leftover_qty
            if self.insert_data.e_qty <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Erected quantity must be greater than 0"
                )

            if transport_row.t_leftover_qty is None or transport_row.t_leftover_qty <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="No remaining quantity available for erection from this transport"
                )

            if self.insert_data.e_qty > transport_row.t_leftover_qty:
                raise HTTPException(
                    status_code=400,
                    detail=f"Erected quantity ({self.insert_data.e_qty}) cannot exceed available leftover ({transport_row.t_leftover_qty})"
                )

            # 3. Find ANY Combine record to get main_id
            # combine_query = select(Combine).where(
            #     Combine.transport_id == self.insert_data.transport_id
            # ).limit(1)
            # combine_result = await self.db.execute(combine_query)
            # combine_row = combine_result.scalars().first()
            #
            # if not combine_row or not combine_row.main_id:
            #     raise HTTPException(
            #         status_code=404,
            #         detail=f"No linked main record found for transport {self.insert_data.transport_id}"
            #     )
            #
            # main_id = combine_row.main_id
            main_id = transport_row.main_id

            if not main_id:
                raise HTTPException(
                    status_code=404,
                    detail=f"No linked main record found for transport {self.insert_data.transport_id}"
                )

            # 4. Get Mains record for area and weight
            main_query = select(Mains).where(Mains.id == main_id)
            main_result = await self.db.execute(main_query)
            main_row = main_result.scalar_one_or_none()

            if not main_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Main record with id {main_id} not found"
                )

            # 5. Calculate weight: main.weight * e_qty
            calculated_weight = main_row.weight * self.insert_data.e_qty if main_row.weight else 0

            # 6. Create Erected record
            erected_record = Erected(
                area=main_row.area,
                structure=transport_row.structure_2,
                row_labels=transport_row.raw_labels,
                mark_names=transport_row.mark_name,
                e_qty=self.insert_data.e_qty,
                e_weight=calculated_weight,
                daily_e_date=date.today(),
                proce_qty=transport_row.proce_qty,
                altitude_mark_1=self.insert_data.altitude_mark_1,
                altitude_mark_2=self.insert_data.altitude_mark_2,
                axis=self.insert_data.axis,
                range=self.insert_data.range,
                created_by=self.insert_data.created_by
            )

            self.db.add(erected_record)
            await self.db.flush()

            # 7. Deduct from transport leftover
            transport_row.t_leftover_qty -= self.insert_data.e_qty

            # 8. Create NEW Combine record
            new_combine = Combine(
                transport_id=transport_row.id,
                main_id=main_id,
                erected_id=erected_record.id
            )
            self.db.add(new_combine)

            # 9. Commit everything
            await self.db.commit()
            await self.db.refresh(erected_record)
            await self.db.refresh(transport_row)
            await self.db.refresh(new_combine)

            return {
                "success": True,
                "message": "Erected record created successfully",
                "data": {
                    "erected_id": erected_record.id,
                    "transport_id": transport_row.id,
                    "main_id": main_id,
                    "combine_id": new_combine.id,
                    "e_qty": self.insert_data.e_qty,
                    "e_weight": calculated_weight,
                    "date": str(date.today()),
                    "area": main_row.area,
                    "structure": transport_row.structure_2,
                    "mark_names": transport_row.mark_name,
                    "altitude_mark_1": self.insert_data.altitude_mark_1,
                    "altitude_mark_2": self.insert_data.altitude_mark_2,
                    "axis": self.insert_data.axis,
                    "range": self.insert_data.range,
                    "transport_leftover_qty": transport_row.t_leftover_qty
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Failed to insert erected record: {str(e)}")


class ImportTransportDataRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.batch_size = 1000
        self.errors = []
        self.success_count = 0
        self.excel_path = Path("static_datas/transport_data.xlsx")

    async def import_transport_data(self):
        try:
            # 1. Read Excel file
            if not self.excel_path.exists():
                raise HTTPException(status_code=404, detail=f"File not found: {self.excel_path}")

            df = pd.read_excel(self.excel_path)

            # 2. Normalize column names (strip spaces, lowercase for matching)
            df.columns = [col.strip().lower() for col in df.columns]

            # 3. Rename columns to match our model if needed
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
                'location': 'location',
            }

            # Only keep columns that exist in the Excel
            existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df[list(existing_columns.keys())].rename(columns=existing_columns)

            total_rows = len(df)

            # 4. Process in batches
            for batch_start in range(0, total_rows, self.batch_size):
                batch_end = min(batch_start + self.batch_size, total_rows)
                batch = df.iloc[batch_start:batch_end]

                await self._process_batch(batch, batch_start)

            # 5. Commit all successful imports
            await self.db.commit()

            return {
                "total_rows": total_rows,
                "successful_imports": self.success_count,
                "errors": self.errors[-100:] if len(self.errors) > 100 else self.errors  # Return last 100 errors
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Import failed: {str(e)}")

    async def _process_batch(self, batch, batch_start):
        """Process a batch of rows"""
        for idx, row in batch.iterrows():
            excel_row_num = batch_start + idx + 2

            try:
                # Skip completely empty rows
                if pd.isna(row.get('structure_2')) and pd.isna(row.get('mark_name')):
                    continue

                # Find matching Main record
                main_record = await self._find_main(row)

                if not main_record:
                    self.errors.append({
                        "row": excel_row_num,
                        "structure_2": str(row.get('structure_2', 'N/A')),
                        "mark_name": str(row.get('mark_name', 'N/A')),
                        "error": "No matching Main record found"
                    })
                    continue

                # Parse values
                t_qty = self._parse_float(row.get('t_qty'))
                t_weight = self._parse_float(row.get('t_weight'))
                t_date = self._parse_date(row.get('t_date'))
                proce_qty = self._parse_int(row.get('proce_qty'))

                # Create Transport record
                transport = TransportModel(
                    main_id=main_record.id,
                    structure_1=self._parse_str(row.get('structure_1')),
                    structure_2=self._parse_str(row.get('structure_2')),
                    raw_labels=self._parse_str(row.get('raw_labels')),
                    mark_name=self._parse_str(row.get('mark_name')),
                    t_qty=t_qty,
                    t_leftover_qty=t_qty,
                    t_weight=t_weight,
                    t_date=t_date,
                    t_status=self._parse_str(row.get('t_status')),
                    proce_qty=proce_qty,
                    order_no=self._parse_str(row.get('order_no')),
                    key=self._parse_str(row.get('key')),
                    area=self._parse_str(row.get('area')),
                    location=self._parse_str(row.get('location')),
                    created_by=None
                )

                self.db.add(transport)

                # 🔥 Deduct from mains.left_over_qty
                if t_qty is not None:
                    if main_record.left_over_qty is not None:
                        main_record.left_over_qty -= t_qty
                    elif main_record.qty is not None:
                        main_record.left_over_qty = main_record.qty - t_qty

                self.success_count += 1

            except Exception as e:
                self.errors.append({
                    "row": excel_row_num,
                    "structure_2": str(row.get('structure_2', 'N/A')),
                    "mark_name": str(row.get('mark_name', 'N/A')),
                    "error": str(e)
                })

    async def _find_main(self, row):
        """Find matching Main record using key + item"""
        structure_2 = self._parse_str(row.get('structure_2'))
        mark_name = self._parse_str(row.get('mark_name'))

        if not structure_2 or not mark_name:
            return None

        # Level 1: Match by key + item + row_labels + qty
        row_labels = self._parse_str(row.get('raw_labels'))
        proce_qty = self._parse_float(row.get('proce_qty'))

        if row_labels and proce_qty:
            query = select(Mains).where(
                Mains.key == structure_2,
                Mains.item == mark_name,
                Mains.row_labels == row_labels,
                Mains.qty == proce_qty
            )
            result = await self.db.execute(query)
            main = result.scalar_one_or_none()
            if main:
                return main

        # Level 2: Match by key + item + row_labels
        if row_labels:
            query = select(Mains).where(
                Mains.key == structure_2,
                Mains.item == mark_name,
                Mains.row_labels == row_labels
            )
            result = await self.db.execute(query)
            main = result.scalar_one_or_none()
            if main:
                return main

        # Level 3: Match by key + item only
        query = select(Mains).where(
            Mains.key == structure_2,
            Mains.item == mark_name
        )
        result = await self.db.execute(query)
        main = result.scalar_one_or_none()
        if main:
            return main

        # Level 4: Match by key only (last resort)
        query = select(Mains).where(Mains.key == structure_2)
        result = await self.db.execute(query)
        main = result.scalar_one_or_none()
        return main

    # Helper methods
    def _parse_str(self, value):
        """Parse string value from Excel cell"""
        if pd.isna(value) or value == 'N/A' or value == '':
            return None
        return str(value).strip()

    def _parse_float(self, value):
        """Parse float value from Excel cell"""
        if pd.isna(value) or value == 'N/A' or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value):
        """Parse integer value from Excel cell"""
        if pd.isna(value) or value == 'N/A' or value == '':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def _parse_date(self, value):
        """Parse date value from Excel cell"""
        if pd.isna(value) or value == 'N/A' or value == '':
            return date.today()
        try:
            # Handle Excel serial date number
            if isinstance(value, (int, float)):
                from datetime import datetime as dt, timedelta
                # Excel epoch starts at 1899-12-30
                excel_epoch = dt(1899, 12, 30)
                return (excel_epoch + timedelta(days=int(value))).date()

            # Handle datetime objects
            if isinstance(value, datetime):
                return value.date()

            # Handle string dates
            return pd.to_datetime(value).date()
        except Exception:
            return date.today()


