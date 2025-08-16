from models.bill_model import BillModel
from services.ai_service import AISplitService

class BillService:
    def __init__(self):
        self.bill_model = BillModel()
        self.split_service = AISplitService()

    def create_bill(self, bill_data: dict):
        bill = self.bill_model.create_bill(bill_data)

        manual_split = bill_data.get("manual_split", False)
        splits = []

        if not manual_split:
            splits = self.split_service.auto_generate(bill["bill_id"], bill["total_amount"])

        return {"bill": bill, "splits": splits}
