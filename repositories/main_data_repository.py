

class ImportMainDataRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def import_static_main_data(self):
        pass