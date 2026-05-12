from typing import Optional
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import selectinload
from models.main_models import Mains, TransportModel, Erected, Combine


class FetchAllCombineRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_all_combine_data(
        self,
        limit: int = 100,
        offset: int = 0,
        # Main filters
        main_area: Optional[str] = None,
        main_zone: Optional[str] = None,
        main_item: Optional[str] = None,
        # Transport filters
        transport_status: Optional[str] = None,
        transport_date_from: Optional[str] = None,
        transport_date_to: Optional[str] = None,
        # Erected filters
        erected_date_from: Optional[str] = None,
        erected_date_to: Optional[str] = None,
        # Global search
        search: Optional[str] = None,
    ):
        try:
            # Base query with eager loading
            query = (
                select(Combine)
                .options(
                    selectinload(Combine.main),
                    selectinload(Combine.transport),
                    selectinload(Combine.erected)
                )
            )

            # Join for filtering
            query = query.join(Mains, Combine.main_id == Mains.id, isouter=True)
            query = query.join(TransportModel, Combine.transport_id == TransportModel.id, isouter=True)
            query = query.join(Erected, Combine.erected_id == Erected.id, isouter=True)

            # Apply filters
            filter_conditions = []

            # Main filters
            if main_area:
                filter_conditions.append(Mains.area.ilike(f"%{main_area}%"))
            if main_zone:
                filter_conditions.append(Mains.zone.ilike(f"%{main_zone}%"))
            if main_item:
                filter_conditions.append(Mains.item.ilike(f"%{main_item}%"))

            # Transport filters
            if transport_status:
                filter_conditions.append(TransportModel.t_status == transport_status)
            if transport_date_from:
                filter_conditions.append(TransportModel.t_date >= transport_date_from)
            if transport_date_to:
                filter_conditions.append(TransportModel.t_date <= transport_date_to)

            # Erected filters
            if erected_date_from:
                filter_conditions.append(Erected.daily_e_date >= erected_date_from)
            if erected_date_to:
                filter_conditions.append(Erected.daily_e_date <= erected_date_to)

            # Global search across multiple fields
            if search:
                search_filter = or_(
                    Mains.area.ilike(f"%{search}%"),
                    Mains.zone.ilike(f"%{search}%"),
                    Mains.key.ilike(f"%{search}%"),
                    Mains.item.ilike(f"%{search}%"),
                    Mains.description.ilike(f"%{search}%"),
                    Mains.dwgn.ilike(f"%{search}%"),
                    TransportModel.mark_name.ilike(f"%{search}%"),
                    TransportModel.order_no.ilike(f"%{search}%"),
                    TransportModel.key.ilike(f"%{search}%"),
                    TransportModel.area.ilike(f"%{search}%"),
                    TransportModel.location.ilike(f"%{search}%"),
                    Erected.mark_names.ilike(f"%{search}%"),
                )
                filter_conditions.append(search_filter)

            if filter_conditions:
                query = query.where(and_(*filter_conditions))

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_count = await self.db.scalar(count_query)

            # Apply pagination
            query = query.offset(offset).limit(limit)

            # Execute
            result = await self.db.execute(query)
            combine_rows = result.unique().scalars().all()

            # Serialize
            data = []
            for combine in combine_rows:
                row = {
                    "combine_id": combine.id,
                    "main": self._serialize_main(combine.main) if combine.main else None,
                    "transport": self._serialize_transport(combine.transport) if combine.transport else None,
                    "erected": self._serialize_erected(combine.erected) if combine.erected else None,
                }
                data.append(row)

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
                    "main_area": main_area,
                    "main_zone": main_zone,
                    "main_item": main_item,
                    "transport_status": transport_status,
                    "transport_date_from": transport_date_from,
                    "transport_date_to": transport_date_to,
                    "erected_date_from": erected_date_from,
                    "erected_date_to": erected_date_to,
                    "search": search
                }
            }

        except Exception as e:
            raise Exception(f"Failed to fetch combine data: {str(e)}")

    def _serialize_main(self, main):
        if not main:
            return None
        return {
            "id": main.id,
            "area": main.area,
            "zone": main.zone,
            "key": main.key,
            "row_labels": main.row_labels,
            "item": main.item,
            "p_s": main.p_s,
            "qty": main.qty,
            "left_over_qty": main.left_over_qty,
            "description": main.description,
            "section": main.section,
            "length": main.length,
            "weight": main.weight,
            "weight_total": main.weight_total,
            "dwgn": main.dwgn,
        }

    def _serialize_transport(self, transport):
        if not transport:
            return None
        return {
            "id": transport.id,
            "structure_1": transport.structure_1,
            "structure_2": transport.structure_2,
            "raw_labels": transport.raw_labels,
            "mark_name": transport.mark_name,
            "t_qty": transport.t_qty,
            "t_leftover_qty": transport.t_leftover_qty,
            "t_weight": transport.t_weight,
            "t_date": str(transport.t_date) if transport.t_date else None,
            "t_status": transport.t_status,
            "proce_qty": transport.proce_qty,
            "order_no": transport.order_no,
            "key": transport.key,
            "area": transport.area,
            "location": transport.location,
            "created_by": transport.created_by,
            "created_at": str(transport.created_at) if transport.created_at else None,
            "updated_at": str(transport.updated_at) if transport.updated_at else None,
        }

    def _serialize_erected(self, erected):
        if not erected:
            return None
        return {
            "id": erected.id,
            "area": erected.area,
            "structure": erected.structure,
            "row_labels": erected.row_labels,
            "mark_names": erected.mark_names,
            "e_qty": erected.e_qty,
            "e_weight": erected.e_weight,
            "daily_e_date": str(erected.daily_e_date) if erected.daily_e_date else None,
            "proce_qty": erected.proce_qty,
            "altitude_mark_1": erected.altitude_mark_1,
            "altitude_mark_2": erected.altitude_mark_2,
            "axis": erected.axis,
            "range": erected.range,
            "created_by": erected.created_by,
        }