from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.sql import func

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date  # Add 'date' here
import json
from typing import Optional

from models.main_models import Erected




class FetchErectedDataRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_erected_data(
            self,
            limit: int = 100,
            offset: int = 0,
            # Filters
            area: Optional[str] = None,
            structure: Optional[str] = None,
            row_labels: Optional[str] = None,
            mark_names: Optional[str] = None,
            altitude_mark_1: Optional[str] = None,
            axis: Optional[str] = None,
            range: Optional[str] = None,
            altitude_mark_2: Optional[str] = None,
            # Range filters
            min_e_qty: Optional[float] = None,
            max_e_qty: Optional[float] = None,
            min_e_weight: Optional[float] = None,
            max_e_weight: Optional[float] = None,
            min_proce_qty: Optional[float] = None,
            max_proce_qty: Optional[float] = None,
            # Date filters
            daily_e_date_from: Optional[date] = None,
            daily_e_date_to: Optional[date] = None,
            # Global search
            search: Optional[str] = None
    ):
        try:
            # Build query
            query = select(Erected)

            # Apply filters
            if area:
                query = query.where(Erected.area == area)

            if structure:
                query = query.where(Erected.structure.ilike(f"%{structure}%"))

            if row_labels:
                query = query.where(Erected.row_labels.ilike(f"%{row_labels}%"))

            if mark_names:
                query = query.where(Erected.mark_names.ilike(f"%{mark_names}%"))

            if altitude_mark_1:
                query = query.where(Erected.altitude_mark_1.ilike(f"%{altitude_mark_1}%"))

            if axis:
                query = query.where(Erected.axis.ilike(f"%{axis}%"))

            if range:
                query = query.where(Erected.range.ilike(f"%{range}%"))

            if altitude_mark_2:
                query = query.where(Erected.altitude_mark_2.ilike(f"%{altitude_mark_2}%"))

            # Range filters
            if min_e_qty is not None:
                query = query.where(Erected.e_qty >= min_e_qty)
            if max_e_qty is not None:
                query = query.where(Erected.e_qty <= max_e_qty)

            if min_e_weight is not None:
                query = query.where(Erected.e_weight >= min_e_weight)
            if max_e_weight is not None:
                query = query.where(Erected.e_weight <= max_e_weight)

            if min_proce_qty is not None:
                query = query.where(Erected.proce_qty >= min_proce_qty)
            if max_proce_qty is not None:
                query = query.where(Erected.proce_qty <= max_proce_qty)

            # Date filters
            if daily_e_date_from:
                query = query.where(Erected.daily_e_date >= daily_e_date_from)
            if daily_e_date_to:
                query = query.where(Erected.daily_e_date <= daily_e_date_to)

            # Global search across multiple fields
            if search:
                search_filter = or_(
                    Erected.area.ilike(f"%{search}%"),
                    Erected.structure.ilike(f"%{search}%"),
                    Erected.row_labels.ilike(f"%{search}%"),
                    Erected.mark_names.ilike(f"%{search}%"),
                    Erected.altitude_mark_1.ilike(f"%{search}%"),
                    Erected.axis.ilike(f"%{search}%"),
                    Erected.range.ilike(f"%{search}%"),
                    Erected.altitude_mark_2.ilike(f"%{search}%")
                )
                query = query.where(search_filter)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_count = await self.db.scalar(count_query)

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
                    "structure": item.structure,
                    "row_labels": item.row_labels,
                    "mark_names": item.mark_names,
                    "e_qty": item.e_qty,
                    "e_weight": item.e_weight,
                    "daily_e_date": item.daily_e_date.isoformat() if item.daily_e_date else None,
                    "proce_qty": item.proce_qty,
                    "altitude_mark_1": item.altitude_mark_1,
                    "axis": item.axis,
                    "range": item.range,
                    "altitude_mark_2": item.altitude_mark_2
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
                    "structure": structure,
                    "row_labels": row_labels,
                    "mark_names": mark_names,
                    "altitude_mark_1": altitude_mark_1,
                    "axis": axis,
                    "range": range,
                    "altitude_mark_2": altitude_mark_2,
                    "min_e_qty": min_e_qty,
                    "max_e_qty": max_e_qty,
                    "min_e_weight": min_e_weight,
                    "max_e_weight": max_e_weight,
                    "min_proce_qty": min_proce_qty,
                    "max_proce_qty": max_proce_qty,
                    "daily_e_date_from": daily_e_date_from.isoformat() if daily_e_date_from else None,
                    "daily_e_date_to": daily_e_date_to.isoformat() if daily_e_date_to else None,
                    "search": search
                }
            }

        except Exception as e:
            raise Exception(f"Failed to fetch erected data: {str(e)}")

    async def get_unique_values(self, column_name: str):
        """Get unique values for a specific column"""
        try:
            column = getattr(Erected, column_name, None)
            if not column:
                raise ValueError(f"Column '{column_name}' does not exist in Erected model")

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

    async def get_statistics(self):
        """Get statistics for erected data"""
        try:
            # Total count
            total_count_query = select(func.count()).select_from(Erected)
            total_count = await self.db.scalar(total_count_query)

            # Summary statistics
            stats_query = select(
                func.avg(Erected.e_qty).label("avg_e_qty"),
                func.max(Erected.e_qty).label("max_e_qty"),
                func.min(Erected.e_qty).label("min_e_qty"),
                func.avg(Erected.e_weight).label("avg_e_weight"),
                func.max(Erected.e_weight).label("max_e_weight"),
                func.min(Erected.e_weight).label("min_e_weight"),
                func.avg(Erected.proce_qty).label("avg_proce_qty"),
                func.max(Erected.proce_qty).label("max_proce_qty"),
                func.min(Erected.proce_qty).label("min_proce_qty"),
                func.count(Erected.area.distinct()).label("unique_areas"),
                func.count(Erected.structure.distinct()).label("unique_structures"),
                func.count(Erected.axis.distinct()).label("unique_axes"),
                func.min(Erected.daily_e_date).label("earliest_date"),
                func.max(Erected.daily_e_date).label("latest_date")
            )

            result = await self.db.execute(stats_query)
            stats = result.one()

            return {
                "success": True,
                "total_records": total_count,
                "statistics": {
                    "e_qty": {
                        "average": float(stats.avg_e_qty) if stats.avg_e_qty else None,
                        "maximum": float(stats.max_e_qty) if stats.max_e_qty else None,
                        "minimum": float(stats.min_e_qty) if stats.min_e_qty else None
                    },
                    "e_weight": {
                        "average": float(stats.avg_e_weight) if stats.avg_e_weight else None,
                        "maximum": float(stats.max_e_weight) if stats.max_e_weight else None,
                        "minimum": float(stats.min_e_weight) if stats.min_e_weight else None
                    },
                    "proce_qty": {
                        "average": float(stats.avg_proce_qty) if stats.avg_proce_qty else None,
                        "maximum": float(stats.max_proce_qty) if stats.max_proce_qty else None,
                        "minimum": float(stats.min_proce_qty) if stats.min_proce_qty else None
                    },
                    "unique_values": {
                        "areas": int(stats.unique_areas) if stats.unique_areas else 0,
                        "structures": int(stats.unique_structures) if stats.unique_structures else 0,
                        "axes": int(stats.unique_axes) if stats.unique_axes else 0
                    },
                    "date_range": {
                        "earliest": stats.earliest_date.isoformat() if stats.earliest_date else None,
                        "latest": stats.latest_date.isoformat() if stats.latest_date else None
                    }
                }
            }
        except Exception as e:
            raise Exception(f"Failed to get statistics: {str(e)}")





class ImportErectedDataRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def import_erected_main_data(self):
        error_log = []
        imported_count = 0
        skipped_count = 0

        try:
            # Define the path to Excel file
            excel_path = Path("static_datas/erected_data.xlsx")

            if not excel_path.exists():
                raise FileNotFoundError(f"Excel file not found at {excel_path}")

            # Create error log file
            log_filename = f"error_log_erected_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Read entire Excel file
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
                float_columns = ['e_qty', 'e_weight', 'proce_qty']
                for col in float_columns:
                    if col in chunk.columns:
                        chunk[col] = pd.to_numeric(chunk[col], errors='coerce')
                        chunk[col] = chunk[col].where(pd.notnull(chunk[col]), None)

                # Convert date column
                if 'daily_e_date' in chunk.columns:
                    chunk['daily_e_date'] = pd.to_datetime(chunk['daily_e_date'], errors='coerce')
                    chunk['daily_e_date'] = chunk['daily_e_date'].where(pd.notnull(chunk['daily_e_date']), None)

                # Process each row in the chunk
                for idx, row in chunk.iterrows():
                    try:
                        # Create Erected instance
                        erected_record = Erected(
                            area=self._clean_string(row.get('area')),
                            structure=self._clean_string(row.get('structure')),
                            row_labels=self._clean_string(row.get('row_labels')),
                            mark_names=self._clean_string(row.get('mark_names')),
                            e_qty=self._clean_float(row.get('e_qty')),
                            e_weight=self._clean_float(row.get('e_weight')),
                            daily_e_date=self._clean_date(row.get('daily_e_date')),
                            proce_qty=self._clean_float(row.get('proce_qty')),
                            altitude_mark_1=self._clean_string(row.get('altitude_mark_1')),
                            axis=self._clean_string(row.get('axis')),
                            range=self._clean_string(row.get('range')),
                            altitude_mark_2=self._clean_string(row.get('altitude_mark_2'))
                        )

                        self.db.add(erected_record)
                        imported_count += 1

                        # Flush every 500 records
                        if imported_count % 500 == 0:
                            await self.db.flush()

                    except Exception as e:
                        skipped_count += 1
                        error_entry = {
                            "row_number": idx + 2,
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
            raise Exception(f"Failed to import erected data: {str(e)}")

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

    def _clean_date(self, value):
        """Clean date values"""
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        if isinstance(value, datetime):
            return value.date()
        try:
            if isinstance(value, str):
                return datetime.strptime(value, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
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
            elif isinstance(value, datetime):
                clean_dict[key] = value.isoformat()
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

