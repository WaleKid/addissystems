dispatch_avro = {
    "type": "record",
    "name": "dispatch_avro_schema",
    "fields": [{
        "name": "Dispatch_ref",
        "type": [{
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
                    {"name": "Dispatch_note_number", "type": "string"}
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
        {"name": "Invoice_allowance", "type": ["null", "int"]},
        {"name": "Invoice_charge", "type": ["null", "int"]},
        {
            "name": "Invoice_line",
            "type": ["null", {
                "type": "array",
                "items": ["null", {
                    "type": "record",
                    "name": "Invoice_line",
                    "fields": [
                        {"name": "Line_allowance_amount", "type": "string"},
                        {"name": "Line_allowance_code", "type": "string"},
                        {"name": "Line_allowance_reason", "type": "string"},
                        {"name": "Line_charge_amount", "type": "string"},
                        {"name": "Line_charge_code", "type": "string"},
                        {"name": "Line_charge_reason", "type": "string"},
                        {"name": "barcode", "type": "string"},
                        {"name": "hsncode", "type": "string"},
                        {"name": "item_name", "type": "string"},
                        {"name": "price", "type": "string"},
                        {"name": "qty", "type": "string"},
                        {"name": "sno", "type": "string"},
                        {"name": "tax", "type": "string"},
                        {"name": "total_price", "type": "string"},
                        {"name": "unit", "type": "string"
                    }]
                }]
            }]
        },
        {"name": "Invoice_total", "type": "string"},
        {
            "name": "Vat_breakdown",
            "type": ["null", {
                "type": "record",
                "name": "Vat_breakdown",
                "fields": [
                    {"name": "Vat_breakdown_amount", "type": "string"},
                    {"name": "Vat_category_code", "type": "string"},
                    {"name": "Vat_reason_code", "type": "string"},
                    {"name": "Vat_reason_text", "type": "string"
                }]
            }]
        }, {
            "name": "payee",
            "type": ["null", {
                "type": "record",
                "name": "Payee",
                "fields": [
                    {"name": "bank", "type": "string"},
                    {"name": "bank_account", "type": "string"},
                    {"name": "id","type": "string"},
                    {"name": "legal_registration", "type": "string"},
                    {"name": "name", "type": "string"},
                    {"name": "registration_number","type": "string"}
                ]
            }]
        }]
}
