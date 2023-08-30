dispatch_avro = {
    "type": "record",
    "name": "dispatch_avro_schema",
    "fields": [{
        "name": "Dispatch_ref",
        "type": [{
            "type": "record",
            "name": "dispatch_ref",
            "fields": [
                {"name": "Buyer_ref_no", "type": "string"},
                {"name": "Contrat_ref_no", "type": "string"},
                {"name": "Seller_order_ref_no", "type": "string"},
                {"name": "Rec_advice_ref_no", "type": "string"},
                {"name": "Dispatch_ref", "type": "string"},
                {"name": "Disp_advice_ref_no", "type": "string"},
                {"name": "Tender_ref_no", "type": "string"}
            ]
        }]
    },
        {
            "name": "Seller",
            "type": ["null", {
                "type": "record",
                "name": "Seller",
                "fields": [
                    {"name": "company_name", "type": "string"},
                    {"name": "licence_number", "type": "string"},
                    {"name": "tin_no", "type": "string"},
                    {"name": "vat_reg_Dt", "type": "string"},
                    {"name": "vat_reg_no", "type": "string"}
                ]
            }]

        },
        {
            "name": "Buyer",
            "type": ["null", {
                "type": "record",
                "name": "Buyer",
                "fields": [
                    {"name": "address", "type": "string"},
                    {"name": "buyer_name", "type": "string"},
                    {"name": "email", "type": "string"},
                    {"name": "location", "type": "string"},
                    {"name": "phone_no", "type": "string"},
                    {"name": "tin_no", "type": "string"},
                    {"name": "vat_reg_no", "type": "string"}
                ]
            }]
        },
        {
            "name": "Dispatch_info",
            "type": ["null", {
                "type": "record",
                "name": "Dispatch_info",
                "fields": [
                    {"name": "Dispatch_number", "type": "string"},
                    {"name": "Dispatch_date", "type": "string"},
                    {"name": "Dispatch_location", "type": "string"},
                    {"name": "Dispatch_note_number", "type": "string"},
                    {"name": "Backorder", "type": "string"}
                ]
            }]
        },
        {
            "name": "Delivery_info",
            "type": ["null", {
                "type": "record",
                "name": "Delivery_info",
                "fields": [
                    {"name": "Delivery_address", "type": "string"},
                    {"name": "Delivery_date", "type": "string"},
                    {"name": "Delivery_location", "type": "string"},
                    {"name": "Delivery_note_number", "type": "string"}
                ]
            }]
        },
        {
            "name": "Stock_Move_line",
            "type": ["null", {
                "type": "array",
                "items": ["null", {
                    "type": "record",
                    "name": "Stock_Move_line",
                    "fields": [
                        {"name": "sno", "type": "string"},
                        {"name": "product_name", "type": "string"},
                        {"name": "product_UoM", "type": "string"},
                        {"name": "product_qty", "type": "string"},
                        {"name": "product_UoM_quantity", "type": "string"},
                        {"name": "quantity_done", "type": "string"},
                        {"name": "hsncode", "type": "string"}
                    ]
                }]
            }]
        }]
}
