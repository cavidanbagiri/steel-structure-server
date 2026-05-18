import json
from pathlib import Path
from datetime import date, datetime
import pandas as pd
import numpy as np
from typing import Optional

from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, and_, func
from sqlalchemy.sql import func


from models.main_models import Erected, Mains, TransportModel, Combine



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





# class ImportErectedDataRepository:
#
#     def __init__(self, db: AsyncSession):
#         self.db = db
#
#     async def import_erected_main_data(self):
#         error_log = []
#         imported_count = 0
#         skipped_count = 0
#
#         try:
#             # Define the path to Excel file
#             excel_path = Path("static_datas/erected_data.xlsx")
#
#             if not excel_path.exists():
#                 raise FileNotFoundError(f"Excel file not found at {excel_path}")
#
#             # Create error log file
#             log_filename = f"error_log_erected_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
#
#             # Read entire Excel file
#             df = pd.read_excel(excel_path)
#             total_rows = len(df)
#
#             # Process in chunks manually
#             chunk_size = 1000
#
#             for start_idx in range(0, total_rows, chunk_size):
#                 end_idx = min(start_idx + chunk_size, total_rows)
#                 chunk = df.iloc[start_idx:end_idx]
#
#                 # Clean the data
#                 chunk = chunk.replace({np.nan: None, np.inf: None, -np.inf: None})
#
#                 # Convert float columns properly
#                 float_columns = ['e_qty', 'e_weight', 'proce_qty']
#                 for col in float_columns:
#                     if col in chunk.columns:
#                         chunk[col] = pd.to_numeric(chunk[col], errors='coerce')
#                         chunk[col] = chunk[col].where(pd.notnull(chunk[col]), None)
#
#                 # Convert date column
#                 if 'daily_e_date' in chunk.columns:
#                     chunk['daily_e_date'] = pd.to_datetime(chunk['daily_e_date'], errors='coerce')
#                     chunk['daily_e_date'] = chunk['daily_e_date'].where(pd.notnull(chunk['daily_e_date']), None)
#
#                 # Process each row in the chunk
#                 for idx, row in chunk.iterrows():
#                     try:
#                         # Create Erected instance
#                         erected_record = Erected(
#                             area=self._clean_string(row.get('area')),
#                             structure=self._clean_string(row.get('structure')),
#                             row_labels=self._clean_string(row.get('row_labels')),
#                             mark_names=self._clean_string(row.get('mark_names')),
#                             e_qty=self._clean_float(row.get('e_qty')),
#                             e_weight=self._clean_float(row.get('e_weight')),
#                             daily_e_date=self._clean_date(row.get('daily_e_date')),
#                             proce_qty=self._clean_float(row.get('proce_qty')),
#                             altitude_mark_1=self._clean_string(row.get('altitude_mark_1')),
#                             axis=self._clean_string(row.get('axis')),
#                             range=self._clean_string(row.get('range')),
#                             altitude_mark_2=self._clean_string(row.get('altitude_mark_2'))
#                         )
#
#                         self.db.add(erected_record)
#                         imported_count += 1
#
#                         # Flush every 500 records
#                         if imported_count % 500 == 0:
#                             await self.db.flush()
#
#                     except Exception as e:
#                         skipped_count += 1
#                         error_entry = {
#                             "row_number": idx + 2,
#                             "error": str(e),
#                             "data": self._safe_serialize_row(row.to_dict())
#                         }
#                         error_log.append(error_entry)
#                         continue
#
#                 # Commit chunk
#                 try:
#                     await self.db.commit()
#                 except Exception as e:
#                     await self.db.rollback()
#                     error_entry = {
#                         "row_number": f"Chunk {start_idx // chunk_size}",
#                         "error": f"Commit error: {str(e)}",
#                         "data": None
#                     }
#                     error_log.append(error_entry)
#                     continue
#
#             # Save error log to file
#             if error_log:
#                 self._save_error_log(log_filename, error_log, imported_count, skipped_count)
#
#             return {
#                 "success": True,
#                 "message": f"Successfully imported {imported_count} records",
#                 "imported_count": imported_count,
#                 "skipped_count": skipped_count,
#                 "error_log_file": log_filename if error_log else None,
#                 "total_rows_processed": total_rows
#             }
#
#         except Exception as e:
#             await self.db.rollback()
#             raise Exception(f"Failed to import erected data: {str(e)}")
#
#     def _clean_string(self, value):
#         """Clean string values, convert NaN to None"""
#         if value is None or (isinstance(value, float) and np.isnan(value)):
#             return None
#         if isinstance(value, str):
#             return value.strip() if value.strip() else None
#         return str(value) if value is not None else None
#
#     def _clean_float(self, value):
#         """Clean float values, convert NaN to None"""
#         if value is None or (isinstance(value, float) and np.isnan(value)):
#             return None
#         if isinstance(value, (int, float)):
#             return float(value)
#         try:
#             return float(value)
#         except (ValueError, TypeError):
#             return None
#
#     def _clean_date(self, value):
#         """Clean date values"""
#         if value is None or (isinstance(value, float) and np.isnan(value)):
#             return None
#         if isinstance(value, datetime):
#             return value.date()
#         try:
#             if isinstance(value, str):
#                 return datetime.strptime(value, '%Y-%m-%d').date()
#         except (ValueError, TypeError):
#             return None
#         return None
#
#     def _safe_serialize_row(self, row_dict):
#         """Safely serialize row data for logging"""
#         clean_dict = {}
#         for key, value in row_dict.items():
#             if isinstance(value, float) and np.isnan(value):
#                 clean_dict[key] = None
#             elif isinstance(value, (np.int64, np.int32)):
#                 clean_dict[key] = int(value)
#             elif isinstance(value, (np.float64, np.float32)):
#                 clean_dict[key] = float(value) if not np.isnan(value) else None
#             elif isinstance(value, datetime):
#                 clean_dict[key] = value.isoformat()
#             else:
#                 clean_dict[key] = value
#         return clean_dict
#
#     def _save_error_log(self, filename, error_log, imported_count, skipped_count):
#         """Save error log to file"""
#         log_data = {
#             "import_date": datetime.now().isoformat(),
#             "total_imported": imported_count,
#             "total_skipped": skipped_count,
#             "errors": error_log
#         }
#
#         log_path = Path("logs") / filename
#         log_path.parent.mkdir(exist_ok=True)
#
#         with open(log_path, 'w', encoding='utf-8') as f:
#             json.dump(log_data, f, indent=2, ensure_ascii=False)
#
#         print(f"Error log saved to: {log_path}")




class ImportErectedDataRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.batch_size = 500  # Smaller batches due to more complex logic
        self.errors = []
        self.unmatched = []
        self.success_count = 0
        self.excel_path = Path("static_datas/erected_data.xlsx")

    async def import_erected_data(self):
        try:
            # 1. Read Excel file
            if not self.excel_path.exists():
                raise HTTPException(status_code=404, detail=f"File not found: {self.excel_path}")

            df = pd.read_excel(self.excel_path)

            # 2. Normalize column names
            df.columns = [col.strip().lower() for col in df.columns]

            # 3. Rename columns to match our model
            column_mapping = {
                'area': 'area',
                'structure': 'structure',
                'row_labels': 'row_labels',
                'mark_names': 'mark_names',
                'e_qty': 'e_qty',
                'e_weight': 'e_weight',
                'daily_e_date': 'daily_e_date',
                'proce_qty': 'proce_qty',
                'altitude_mark_1': 'altitude_mark_1',
                'axis': 'axis',
                'range': 'range',
                'altitude_mark_2': 'altitude_mark_2',
            }

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
                "unmatched_rows": self.unmatched[-100:] if len(self.unmatched) > 100 else self.unmatched,
                "errors": self.errors[-100:] if len(self.errors) > 100 else self.errors
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Import failed: {str(e)}")

    async def _process_batch(self, batch, batch_start):
        """Process a batch of erected rows"""
        for idx, row in batch.iterrows():
            excel_row_num = batch_start + idx + 2

            try:
                # Skip completely empty rows
                if pd.isna(row.get('structure')) and pd.isna(row.get('mark_names')):
                    continue

                structure = self._parse_str(row.get('structure'))
                mark_names = self._parse_str(row.get('mark_names'))
                e_qty = self._parse_float(row.get('e_qty'))

                if not structure or not mark_names:
                    self.errors.append({
                        "row": excel_row_num,
                        "structure": str(row.get('structure', 'N/A')),
                        "mark_names": str(row.get('mark_names', 'N/A')),
                        "error": "Missing structure or mark_names"
                    })
                    continue

                if not e_qty or e_qty <= 0:
                    self.errors.append({
                        "row": excel_row_num,
                        "structure": structure,
                        "mark_names": mark_names,
                        "error": f"Invalid e_qty: {e_qty}"
                    })
                    continue

                # Find matching Main record
                main_record = await self._find_main(row)

                if not main_record:
                    self.unmatched.append({
                        "row": excel_row_num,
                        "structure": structure,
                        "mark_names": mark_names,
                        "error": "No matching Main record found"
                    })
                    continue

                # Find available transports for this main
                transports = await self._find_available_transports(main_record.id)

                if not transports:
                    self.unmatched.append({
                        "row": excel_row_num,
                        "structure": structure,
                        "mark_names": mark_names,
                        "main_id": main_record.id,
                        "error": "No transports with available leftover found"
                    })
                    continue

                # Distribute erected quantity across transports
                distribution, remaining = self._distribute_qty(transports, e_qty)

                if remaining > 0:
                    self.unmatched.append({
                        "row": excel_row_num,
                        "structure": structure,
                        "mark_names": mark_names,
                        "main_id": main_record.id,
                        "e_qty": e_qty,
                        "distributed": e_qty - remaining,
                        "remaining": remaining,
                        "error": f"Not enough transport leftover. Distributed {e_qty - remaining}, remaining {remaining}"
                    })
                    # Still create what we can distribute
                    if not distribution:
                        continue

                # Create Erected records and Combine records
                for dist in distribution:
                    await self._create_erected_with_combine(
                        row=row,
                        main_record=main_record,
                        transport_id=dist['transport_id'],
                        e_qty=dist['e_qty']
                    )

                self.success_count += 1

            except Exception as e:
                self.errors.append({
                    "row": excel_row_num,
                    "structure": str(row.get('structure', 'N/A')),
                    "mark_names": str(row.get('mark_names', 'N/A')),
                    "error": str(e)
                })

    async def _find_main(self, row):
        """Find matching Main record"""
        structure = self._parse_str(row.get('structure'))
        mark_names = self._parse_str(row.get('mark_names'))
        row_labels = self._parse_str(row.get('row_labels'))
        proce_qty = self._parse_float(row.get('proce_qty'))

        if not structure or not mark_names:
            return None

        # Level 1: key + item + row_labels + qty
        if row_labels and proce_qty:
            query = select(Mains).where(
                Mains.key == structure,
                Mains.item == mark_names,
                Mains.row_labels == row_labels,
                Mains.qty == proce_qty
            )
            result = await self.db.execute(query)
            main = result.scalar_one_or_none()
            if main:
                return main

        # Level 2: key + item + row_labels
        if row_labels:
            query = select(Mains).where(
                Mains.key == structure,
                Mains.item == mark_names,
                Mains.row_labels == row_labels
            )
            result = await self.db.execute(query)
            main = result.scalar_one_or_none()
            if main:
                return main

        # Level 3: key + item
        query = select(Mains).where(
            Mains.key == structure,
            Mains.item == mark_names
        )
        result = await self.db.execute(query)
        main = result.scalar_one_or_none()
        if main:
            return main

        # Level 4: key only
        query = select(Mains).where(Mains.key == structure)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _find_available_transports(self, main_id):
        """Find transports with leftover quantity for this main"""
        query = (
            select(TransportModel)
            .where(
                and_(
                    TransportModel.main_id == main_id,
                    TransportModel.t_leftover_qty > 0
                )
            )
            .order_by(TransportModel.id)  # FIFO: oldest first
        )
        result = await self.db.execute(query)
        transports = result.scalars().all()

        return [
            {
                "id": t.id,
                "t_leftover_qty": t.t_leftover_qty,
                "t_qty": t.t_qty
            }
            for t in transports
        ]

    def _distribute_qty(self, transports, e_qty):
        """
        Distribute erected quantity across available transports (FIFO)
        Returns: (distribution_list, remaining_unallocated)
        """
        remaining = e_qty
        distribution = []

        for transport in transports:
            if remaining <= 0:
                break

            available = transport['t_leftover_qty']
            take = min(available, remaining)

            distribution.append({
                'transport_id': transport['id'],
                'e_qty': take
            })

            remaining -= take

        return distribution, remaining

    async def _create_erected_with_combine(self, row, main_record, transport_id, e_qty):
        """Create Erected record and Combine record"""
        # Parse values
        e_weight = self._parse_float(row.get('e_weight'))
        daily_e_date = self._parse_date(row.get('daily_e_date'))
        proce_qty = self._parse_float(row.get('proce_qty'))

        # Create Erected record
        erected = Erected(
            area=self._parse_str(row.get('area')),
            structure=self._parse_str(row.get('structure')),
            row_labels=self._parse_str(row.get('row_labels')),
            mark_names=self._parse_str(row.get('mark_names')),
            e_qty=e_qty,
            e_weight=e_weight,
            daily_e_date=daily_e_date,
            proce_qty=proce_qty,
            altitude_mark_1=self._parse_str(row.get('altitude_mark_1')),
            axis=self._parse_str(row.get('axis')),
            range=self._parse_str(row.get('range')),
            altitude_mark_2=self._parse_str(row.get('altitude_mark_2')),
            created_by=None
        )

        self.db.add(erected)
        await self.db.flush()  # Get erected.id

        # Create Combine record
        combine = Combine(
            transport_id=transport_id,
            main_id=main_record.id,
            erected_id=erected.id
        )
        self.db.add(combine)

        # Deduct from transport leftover
        transport_query = select(TransportModel).where(TransportModel.id == transport_id)
        transport_result = await self.db.execute(transport_query)
        transport_record = transport_result.scalar_one_or_none()

        if transport_record:
            transport_record.t_leftover_qty -= e_qty

    # Helper methods (same as transport import)
    def _parse_str(self, value):
        if pd.isna(value) or value == 'N/A' or value == '':
            return None
        return str(value).strip()

    def _parse_float(self, value):
        if pd.isna(value) or value == 'N/A' or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value):
        if pd.isna(value) or value == 'N/A' or value == '':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def _parse_date(self, value):
        if pd.isna(value) or value == 'N/A' or value == '':
            return date.today()
        try:
            if isinstance(value, (int, float)):
                from datetime import timedelta
                excel_epoch = datetime(1899, 12, 30)
                return (excel_epoch + timedelta(days=int(value))).date()
            if isinstance(value, datetime):
                return value.date()
            return pd.to_datetime(value).date()
        except Exception:
            return date.today()