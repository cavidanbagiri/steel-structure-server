import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date
import json
from io import BytesIO
from typing import Optional

from fastapi.responses import JSONResponse
from fastapi import Depends, Query, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, text
from sqlalchemy.sql import func

from models.main_models import Mains, TransportModel, Combine
from schemas.main_schema import InsertTransportSchema


class ImportMainDataRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def import_static_main_data(self):
        error_log = []
        imported_count = 0
        skipped_count = 0

        try:
            # Define the path to Excel file
            excel_path = Path("static_datas/main_data.xlsx")

            if not excel_path.exists():
                raise FileNotFoundError(f"Excel file not found at {excel_path}")

            # Create error log file
            log_filename = f"error_log_main_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Read entire Excel file first since chunksize doesn't work well
            df = pd.read_excel(excel_path)
            total_rows = len(df)

            # Process in chunks manually
            chunk_size = 1000

            for start_idx in range(0, total_rows, chunk_size):
                end_idx = min(start_idx + chunk_size, total_rows)
                chunk = df.iloc[start_idx:end_idx]

                # Clean the data
                chunk = chunk.replace({np.nan: None, np.inf: None, -np.inf: None})

                # Convert float columns properly
                float_columns = ['qty', 'length', 'weight', 'weight_total']
                for col in float_columns:
                    if col in chunk.columns:
                        chunk[col] = pd.to_numeric(chunk[col], errors='coerce')
                        chunk[col] = chunk[col].where(pd.notnull(chunk[col]), None)

                # Process each row in the chunk
                for idx, row in chunk.iterrows():
                    try:
                        # Validate and clean each value
                        main_record = Mains(
                            area=self._clean_string(row.get('area')),
                            zone=self._clean_string(row.get('zone')),
                            key=self._clean_string(row.get('key')),
                            row_labels=self._clean_string(row.get('row_labels')),
                            item=self._clean_string(row.get('item')),
                            p_s=self._clean_string(row.get('p/s')),
                            qty=self._clean_float(row.get('qty')),
                            left_over_qty=self._clean_float(row.get('qty')),
                            description=self._clean_string(row.get('description')),
                            section=self._clean_string(row.get('section')),
                            length=self._clean_float(row.get('length')),
                            weight=self._clean_float(row.get('weight')),
                            weight_total=self._clean_float(row.get('weight_total')),
                            dwgn=self._clean_string(row.get('dwgn'))
                        )

                        self.db.add(main_record)
                        imported_count += 1

                        # Flush every 500 records
                        if imported_count % 500 == 0:
                            await self.db.flush()

                    except Exception as e:
                        skipped_count += 1
                        error_entry = {
                            "row_number": idx + 2,  # +2 because Excel starts at 1 and header is row 1
                            "error": str(e),
                            "data": self._safe_serialize_row(row.to_dict())
                        }
                        error_log.append(error_entry)
                        continue

                # Commit chunk
                try:
                    await self.db.commit()
                except Exception as e:
                    await self.db.rollback()
                    error_entry = {
                        "row_number": f"Chunk {start_idx // chunk_size}",
                        "error": f"Commit error: {str(e)}",
                        "data": None
                    }
                    error_log.append(error_entry)
                    # Continue with next chunk
                    continue

            # Save error log to file
            if error_log:
                self._save_error_log(log_filename, error_log, imported_count, skipped_count)

            return {
                "success": True,
                "message": f"Successfully imported {imported_count} records",
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "error_log_file": log_filename if error_log else None,
                "total_rows_processed": total_rows
            }

        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Failed to import data: {str(e)}")

    async def import_static_main_data_batch(self):
        """Alternative batch import using execute_many for better performance"""
        error_log = []
        imported_count = 0
        skipped_count = 0

        try:
            excel_path = Path("static_datas/main_data.xlsx")

            if not excel_path.exists():
                raise FileNotFoundError(f"Excel file not found at {excel_path}")

            # Read entire Excel file
            df = pd.read_excel(excel_path)
            df = df.replace({np.nan: None, np.inf: None, -np.inf: None})

            # Prepare batch data
            batch_data = []
            log_filename = f"error_log_main_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            for idx, row in df.iterrows():
                try:
                    # Prepare data dictionary
                    data = {
                        'area': self._clean_string(row.get('area')),
                        'zone': self._clean_string(row.get('zone')),
                        'key': self._clean_string(row.get('key')),
                        'row_labels': self._clean_string(row.get('row_labels')),
                        'item': self._clean_string(row.get('item')),
                        'p_s': self._clean_string(row.get('p/s')),
                        'qty': self._clean_float(row.get('qty')),
                        'description': self._clean_string(row.get('description')),
                        'section': self._clean_string(row.get('section')),
                        'length': self._clean_float(row.get('length')),
                        'weight': self._clean_float(row.get('weight')),
                        'weight_total': self._clean_float(row.get('weight_total')),
                        'dwgn': self._clean_string(row.get('dwgn'))
                    }
                    batch_data.append(data)
                    imported_count += 1

                    # Insert in batches of 1000
                    if len(batch_data) >= 1000:
                        await self._batch_insert(batch_data)
                        batch_data = []

                except Exception as e:
                    skipped_count += 1
                    error_entry = {
                        "row_number": idx + 2,
                        "error": str(e),
                        "data": self._safe_serialize_row(row.to_dict())
                    }
                    error_log.append(error_entry)
                    continue

            # Insert remaining records
            if batch_data:
                await self._batch_insert(batch_data)

            await self.db.commit()

            # Save error log
            if error_log:
                self._save_error_log(log_filename, error_log, imported_count, skipped_count)

            return {
                "success": True,
                "message": f"Successfully imported {imported_count} records",
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "error_log_file": log_filename if error_log else None
            }

        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Failed to import data: {str(e)}")

    async def _batch_insert(self, batch_data):
        """Insert batch of data"""
        insert_query = text("""
            INSERT INTO mains (
                area, zone, key, row_labels, item, p_s, qty, 
                description, section, length, weight, weight_total, dwgn
            ) VALUES (
                :area, :zone, :key, :row_labels, :item, :p_s, :qty,
                :description, :section, :length, :weight, :weight_total, :dwgn
            )
        """)

        for data in batch_data:
            await self.db.execute(insert_query, data)

    def _clean_string(self, value):
        """Clean string values, convert NaN to None"""
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        if isinstance(value, str):
            return value.strip() if value.strip() else None
        return str(value) if value is not None else None

    def _clean_float(self, value):
        """Clean float values, convert NaN to None"""
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_serialize_row(self, row_dict):
        """Safely serialize row data for logging"""
        clean_dict = {}
        for key, value in row_dict.items():
            if isinstance(value, float) and np.isnan(value):
                clean_dict[key] = None
            elif isinstance(value, (np.int64, np.int32)):
                clean_dict[key] = int(value)
            elif isinstance(value, (np.float64, np.float32)):
                clean_dict[key] = float(value) if not np.isnan(value) else None
            else:
                clean_dict[key] = value
        return clean_dict

    def _save_error_log(self, filename, error_log, imported_count, skipped_count):
        """Save error log to file"""
        log_data = {
            "import_date": datetime.now().isoformat(),
            "total_imported": imported_count,
            "total_skipped": skipped_count,
            "errors": error_log
        }

        log_path = Path("logs") / filename
        log_path.parent.mkdir(exist_ok=True)

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"Error log saved to: {log_path}")

    async def preview_file_info(self):
        """Get file information before import"""
        try:
            excel_path = Path("static_datas/main_data.xlsx")

            if not excel_path.exists():
                raise FileNotFoundError(f"Excel file not found at {excel_path}")

            # Read just the first few rows and get info
            df = pd.read_excel(excel_path, nrows=10)
            total_rows = len(pd.read_excel(excel_path))

            # Check for NaN values in each column
            full_df = pd.read_excel(excel_path)
            nan_counts = full_df.isna().sum().to_dict()

            return {
                "file_path": str(excel_path),
                "total_rows": total_rows,
                "columns": list(df.columns),
                "sample_data": df.head(5).replace({np.nan: None}).to_dict(orient='records'),
                "null_counts": {k: int(v) for k, v in nan_counts.items()},
                "file_size_mb": round(excel_path.stat().st_size / (1024 * 1024), 2)
            }

        except Exception as e:
            raise Exception(f"Failed to preview file: {str(e)}")



class FetchMainDataRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_main_data(
            self,
            limit: int = 100,
            offset: int = 0,
            # Filters
            area: Optional[str] = None,
            zone: Optional[str] = None,
            key: Optional[str] = None,
            row_labels: Optional[str] = None,
            item: Optional[str] = None,
            p_s: Optional[str] = None,
            section: Optional[str] = None,
            dwgn: Optional[str] = None,
            qty: Optional[float] = None,
            length: Optional[float] = None,
            weight: Optional[float] = None,
            weight_total: Optional[float] = None,
            search: Optional[str] = None
    ):
        try:
            # Build query
            query = select(Mains)

            # Apply filters
            if area:
                query = query.where(Mains.area == area)

            if zone:
                query = query.where(Mains.zone == zone)

            if key:
                query = query.where(Mains.key.ilike(f"%{key}%"))

            if row_labels:
                query = query.where(Mains.row_labels.ilike(f"%{row_labels}%"))

            if item:
                query = query.where(Mains.item.ilike(f"%{item}%"))

            if p_s:
                query = query.where(Mains.p_s == p_s)

            if section:
                query = query.where(Mains.section.ilike(f"%{section}%"))

            if dwgn:
                query = query.where(Mains.dwgn.ilike(f"%{dwgn}%"))

            if qty:
                query = query.where(Mains.qty == qty)
            if length:
                query = query.where(Mains.length == length)
            if weight:
                query = query.where(Mains.weight == weight)

            if weight_total:
                query = query.where(Mains.weight_total == weight_total)

            # Global search across multiple fields
            if search:
                search_filter = or_(
                    Mains.area.ilike(f"%{search}%"),
                    Mains.zone.ilike(f"%{search}%"),
                    Mains.key.ilike(f"%{search}%"),
                    Mains.row_labels.ilike(f"%{search}%"),
                    Mains.item.ilike(f"%{search}%"),
                    Mains.description.ilike(f"%{search}%"),
                    Mains.section.ilike(f"%{search}%"),
                    Mains.dwgn.ilike(f"%{search}%")
                )
                query = query.where(search_filter)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_count = await self.db.scalar(count_query)

            # 1. Apply Order By (Add this line)
            query = query.order_by(Mains.id.asc())

            # Apply pagination
            query = query.offset(offset).limit(limit)

            # Execute query
            result = await self.db.execute(query)
            items = result.scalars().all()

            # Convert to dict
            data = []
            for item in items:
                data.append({
                    "id": item.id,
                    "area": item.area,
                    "zone": item.zone,
                    "key": item.key,
                    "row_labels": item.row_labels,
                    "item": item.item,
                    "p_s": item.p_s,
                    "qty": item.qty,
                    "left_over_qty": item.left_over_qty,  # ADD THIS
                    "description": item.description,
                    "section": item.section,
                    "length": item.length,
                    "weight": item.weight,
                    "weight_total": item.weight_total,
                    "dwgn": item.dwgn
                })

            return {
                "success": True,
                "data": data,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "next_offset": offset + limit if offset + limit < total_count else None
                },
                "filters_applied": {
                    "area": area,
                    "zone": zone,
                    "key": key,
                    "row_labels": row_labels,
                    "item": item,
                    "p_s": p_s,
                    "section": section,
                    "dwgn": dwgn,
                    "qty": qty,
                    "length": length,
                    "weight": weight,
                    "weight_total": weight_total,
                    "search": search
                }
            }

        except Exception as e:
            raise Exception(f"Failed to fetch main data: {str(e)}")

    async def get_unique_values(self, column_name: str):
        """Get unique values for a specific column (for filter dropdowns)"""
        try:
            column = getattr(Mains, column_name, None)
            if not column:
                raise ValueError(f"Column '{column_name}' does not exist in Mains model")

            query = select(column).where(column.isnot(None)).distinct()
            result = await self.db.execute(query)
            values = result.scalars().all()

            return {
                "success": True,
                "column": column_name,
                "values": sorted([v for v in values if v])
            }
        except Exception as e:
            raise Exception(f"Failed to get unique values: {str(e)}")



class GetRowByIdRepository:
    def __init__(self, db: AsyncSession, id: int):
        self.db = db
        self.id = id

    async def get_row_by_id(self):
        try:
            query = select(Mains).where(Mains.id == self.id)
            result = await self.db.execute(query)
            item = result.scalar_one_or_none()

            if not item:
                raise HTTPException(status_code=404, detail=f"Item with id {self.id} not found")

            data = {
                "id": item.id,
                "area": item.area,
                "zone": item.zone,
                "key": item.key,
                "row_labels": item.row_labels,
                "item": item.item,
                "p_s": item.p_s,
                "qty": item.qty,
                "left_over_qty": item.left_over_qty,  # ADD THIS
                "description": item.description,
                "section": item.section,
                "length": item.length,
                "weight": item.weight,
                "weight_total": item.weight_total,
                "dwgn": item.dwgn
            }

            return {
                "success": True,
                "data": data
            }

        except HTTPException:
            raise
        except Exception as e:
            raise Exception(f"Failed to fetch row by id: {str(e)}")


class InsertToTransportRepository:
    def __init__(self, db: AsyncSession, insert_data: InsertTransportSchema):
        self.db = db
        self.insert_data = insert_data

    async def insert_to_transport(self):
        try:
            # 1. Get the row from main table
            query = select(Mains).where(Mains.id == self.insert_data.row_id)
            result = await self.db.execute(query)
            main_row = result.scalar_one_or_none()

            if not main_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Item with id {self.insert_data.row_id} not found"
                )

            # 2. Check if enough left_over_qty available (NOT qty)
            current_leftover = main_row.left_over_qty if main_row.left_over_qty is not None else main_row.qty

            if current_leftover < self.insert_data.qty:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient quantity. Available: {current_leftover}, Requested: {self.insert_data.qty}"
                )

            # 3. Calculate weight: transport_qty * main.weight
            calculated_weight = self.insert_data.qty * main_row.weight if main_row.weight else 0

            # 4. Create transport record
            transport_record = TransportModel(
                structure_1=main_row.area,
                structure_2=main_row.key,
                key=main_row.key,
                raw_labels=main_row.row_labels,
                mark_name=main_row.item,
                t_qty=self.insert_data.qty,
                t_weight=calculated_weight,
                t_date=date.today(),
                t_status=self.insert_data.status,
                order_no=self.insert_data.order_no,
                area=self.insert_data.area,
                location=self.insert_data.location,
                created_by=self.insert_data.created_by
            )

            self.db.add(transport_record)
            await self.db.flush()  # Get transport_record.id without full commit

            # 5. Deduct from left_over_qty (NOT from qty)
            main_row.left_over_qty = current_leftover - self.insert_data.qty

            # 6. Create Combine record to link main <-> transport
            combine_record = Combine(
                transport_id=transport_record.id,
                main_id=main_row.id,
                erected_id=None
            )
            self.db.add(combine_record)

            # 7. Commit everything
            await self.db.commit()
            await self.db.refresh(transport_record)

            return {
                "success": True,
                "message": "Transport record created successfully",
                "data": {
                    "transport_id": transport_record.id,
                    "main_item_id": main_row.id,
                    "combine_id": combine_record.id,
                    "quantity_transported": self.insert_data.qty,
                    "remaining_leftover": main_row.left_over_qty,
                    "project_qty": main_row.qty,
                    "weight": calculated_weight,
                    "date": str(date.today()),
                    "status": self.insert_data.status,
                    "order_no": self.insert_data.order_no,
                    "area": self.insert_data.area,
                    "location": self.insert_data.location
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Failed to insert transport record: {str(e)}")