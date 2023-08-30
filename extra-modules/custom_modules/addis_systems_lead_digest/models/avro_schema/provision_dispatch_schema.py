provision_dispatch_avro = {
    "type": "record",
    "name": "dispatch_avro_schema",
    "fields": [
        {
        "name": "Dispatch_ref",
        "type": {
            "type": "record",
            "name": "dispatch_ref",
            "fields": [
                {"name": "Buy_ref_no", "type": "string"},
                {"name": "Contrat_ref_no", "type": "string"},
                {"name": "Seller_order_ref_no", "type": "string"},
                {"name": "Rec_advice_ref_no", "type": "string"},
                {"name": "Dispatch_ref", "type": "string"},
                {"name": "Disp_advice_ref_no", "type": "string"},
                {"name": "Tender_ref_no", "type": "string"}
            ]
        }
    },
        {
            "name": "Buyer",
            "type": {
                "type": "record",
                "name": "buyer",
                "fields": [
                    {"name": "address", "type": "string"},
                    {"name": "buyer_name", "type": "string"},
                    {"name": "email", "type": "string"},
                    {"name": "location", "type": "string"},
                    {"name": "phone_no", "type": "string"},
                    {"name": "tin_no", "type": "string"},
                    {"name": "vat_reg_no", "type": "string"}
                ]
            }
        },
        {
            "name": "Dispatch_info",
            "type":  {
                "type": "record",
                "name": "dispatch_info",
                "fields": [
                    {"name": "Dispatch_number", "type": "string"},
                    {"name": "Dispatch_date", "type": "string"},
                    {"name": "Dispatch_location", "type": "string"},
                    {"name": "Dispatch_note_number", "type": "string"},
                ]
            }
        },
        {
            "name": "Delivery_info",
            "type":  {
                "type": "record",
                "name": "delivery_info",
                "fields": [
                    {"name": "Delivery_address", "type": "string"},
                    {"name": "Delivery_date", "type": "string"},
                    {"name": "Delivery_location", "type": "string"},
                    {"name": "Delivery_note_number", "type": "string"}
                ]
            }
        },
        {
            "name": "Dispatch_line",
            "type":  {
                "type": "array",
                "name": "dispatch_line",
                "items":  {
                    "type": "record",
                    "name": "dispatch_line_Items",
                    "fields": [
                        {"name": "sno", "type": "string"},
                        {"name": "item_name", "type": "string"},
                        {"name": "qty", "type": "string"},
                        {"name": "unit", "type": "string"},
                        {"name": "price", "type": "string"}
                    ]
                }
            }
        },
    ]
}
