from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from models.main_models import Mains, TransportModel, Erected, Combine


class FetchMainDataProjectStatisticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_main_data_project_statistics(self):
        """
        Combine all statistics and return
        """
        try:
            mte_weight_statistic = await self.fetch_main_transport_erected_data_statistics()
            main_area_col_statistics = await self.main_area_col_statistics()

            return {
                "success": True,
                "data": {
                    "mte_weight_statistics": mte_weight_statistic,
                    "area_column_statistics": main_area_col_statistics
                }
            }
        except Exception as e:
            raise Exception(f"Failed to fetch project statistics: {str(e)}")

    async def fetch_main_transport_erected_data_statistics(self):
        """
        Returns total weights for main, transport, and erected
        """
        try:
            # Total main weight (sum of all main.weight)
            main_query = select(func.coalesce(func.sum(Mains.weight_total), 0))
            main_result = await self.db.execute(main_query)
            main_total_weight = main_result.scalar()

            # Total transport weight (sum of all transport.t_weight)
            transport_query = select(func.coalesce(func.sum(TransportModel.t_weight), 0))
            transport_result = await self.db.execute(transport_query)
            transport_total_weight = transport_result.scalar()

            # Total erected weight (sum of all erected.e_weight)
            erected_query = select(func.coalesce(func.sum(Erected.e_weight), 0))
            erected_result = await self.db.execute(erected_query)
            erected_total_weight = erected_result.scalar()

            return {
                "main_weight": {
                    "value": round(main_total_weight/1000, 2),
                    "unit": "Ton"
                },
                "transport_weight": {
                    "value": round(transport_total_weight/1000, 2),
                    "unit": "Ton"
                },
                "erected_weight": {
                    "value": round(erected_total_weight/1000, 2),
                    "unit": "Ton"
                }
            }
        except Exception as e:
            raise Exception(f"Failed to fetch MTE weight statistics: {str(e)}")

    async def main_area_col_statistics(self):
        """
        Get unique areas from Mains with weight statistics for main, transport, and erected
        """
        try:
            # Get all unique areas from mains
            areas_query = select(Mains.area).where(Mains.area.isnot(None)).distinct()
            areas_result = await self.db.execute(areas_query)
            areas = [row[0] for row in areas_result.all() if row[0]]

            area_statistics = []

            for area in areas:
                # Main weight for this area
                main_weight_query = select(func.coalesce(func.sum(Mains.weight_total), 0)).where(
                    Mains.area == area
                )
                main_weight_result = await self.db.execute(main_weight_query)
                main_area_weight = main_weight_result.scalar()

                # Transport weight for this area (via transport.main_id -> main.area)
                transport_weight_query = (
                    select(func.coalesce(func.sum(TransportModel.t_weight), 0))
                    .join(Mains, TransportModel.main_id == Mains.id)
                    .where(Mains.area == area)
                )
                transport_weight_result = await self.db.execute(transport_weight_query)
                transport_area_weight = transport_weight_result.scalar()

                # Erected weight for this area (via combine: erected -> combine -> transport -> main)
                erected_weight_query = (
                    select(func.coalesce(func.sum(Erected.e_weight), 0))
                    .join(Combine, Erected.id == Combine.erected_id)
                    .join(TransportModel, Combine.transport_id == TransportModel.id)
                    .join(Mains, TransportModel.main_id == Mains.id)
                    .where(Mains.area == area)
                )
                erected_weight_result = await self.db.execute(erected_weight_query)
                erected_area_weight = erected_weight_result.scalar()

                area_statistics.append({
                    "area": area,
                    "main_weight": {
                        "value": round(main_area_weight, 2),
                        "unit": "Kg"
                    },
                    "transport_weight": {
                        "value": round(transport_area_weight, 2),
                        "unit": "Kg"
                    },
                    "erected_weight": {
                        "value": round(erected_area_weight, 2),
                        "unit": "Kg"
                    }
                })

            return area_statistics

        except Exception as e:
            raise Exception(f"Failed to fetch area column statistics: {str(e)}")