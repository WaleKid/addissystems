refund_schema = {
    "type": "record",
    "name": "invoice_refund",
    "fields": [
        {
            "name": "Invoice_Reference",
            "type": {
                "type": "record",
                "name": "invoice_reference",
                "fields": [
                    {
                        "name": "Buy_ref_no",
                        "type": "string",
                    },
                    {
                        "name": "Seller_ref_no",
                        "type": "string",
                    },
                    {
                        "name": "invoice_declaration",
                        "type": "string",
                    },
                ],
            },
        },
        {
            "name": "Invoice_Desc",
            "type": {
                "type": "record",
                "name": "invoice_desc",
                "fields": [
                    {
                        "name": "taxschema",
                        "type": "string",
                    },
                    {
                        "name": "InvType",
                        "type": "string",
                    },
                    {
                        "name": "Invoice_no",
                        "type": "string",
                    },
                    {
                        "name": "Invoice_ref",
                        "type": "string",
                    },
                    {
                        "name": "Inv_Dt",
                        "type": "string",
                    },
                    {
                        "name": "payment_due_Dt",
                        "type": "string",
                    },
                ],
            },
        },
        {
            "name": "Invoice_source_process",
            "type": {
                "type": "record",
                "name": "invoice_source_process",
                "fields": [
                    {
                        "name": "process",
                        "type": "string",
                    },
                    {
                        "name": "SupType",
                        "type": "string",
                    },
                    {
                        "name": "proccess_reference_no",
                        "type": "string",
                    },
                ],
            },
        },
        {
            "name": "Seller",
            "type": {
                "type": "record",
                "name": "seller",
                "fields": [
                    {
                        "name": "tin_no",
                        "type": "string",
                    },
                    {
                        "name": "license_number",
                        "type": "string",
                    },
                    {
                        "name": "vat_reg_no",
                        "type": "string",
                    },
                    {
                        "name": "vat_reg_Dt",
                        "type": "string",
                    },
                    {
                        "name": "address",
                        "type": "string",
                    },
                    {
                        "name": "company_name",
                        "type": "string",
                    },
                    {
                        "name": "user_name",
                        "type": "string",
                    },
                ],
            },
        },
        {
            "name": "Buyer",
            "type": {
                "type": "record",
                "name": "buyer",
                "fields": [
                    {
                        "name": "tin_no",
                        "type": "string",
                    },
                    {
                        "name": "vat_reg_no",
                        "type": "string",
                    },
                    {
                        "name": "address",
                        "type": "string",
                    },
                    {
                        "name": "location",
                        "type": "string",
                    },
                    {
                        "name": "phone_no",
                        "type": "string",
                    },
                    {
                        "name": "email",
                        "type": "string",
                    },
                    {
                        "name": "company_name",
                        "type": "string",
                    },
                ],
            },
        },
        {
            "name": "Invoice_total",
            "type": "string",
        },
        {
            "name": "Vat_breakdown",
            "type": {
                "type": "record",
                "name": "var_breakdown",
                "fields": [
                    {
                        "name": "Vat_category_code",
                        "type": "string",
                    },
                    {
                        "name": "Vat_reason_code",
                        "type": "string",
                    },
                    {
                        "name": "Vat_reason_text",
                        "type": "string",
                    },
                    {
                        "name": "Vat_breakdown_amount",
                        "type": "string",
                    },
                ],
            },
        },
        {
            "name": "Invoice_allowance",
            "type": "string",
        },
        {
            "name": "Invoice_charge",
            "type": "string",
        },
        {
            "name": "Invoice_line",
            "type": {
                "type": "array",
                "name": "invoice_line",
                "items": {
                    "type": "record",
                    "name": "invoice_line_items",
                    "fields": [
                        {
                            "name": "sno",
                            "type": "string",
                        },
                        {
                            "name": "hsncode",
                            "type": "string",
                        },
                        {
                            "name": "barcode",
                            "type": "string",
                        },
                        {
                            "name": "invoicing_policy",
                            "type": "string",
                        },
                        {
                            "name": "Product_desc",
                            "type": "string",
                        },
                        {
                            "name": "product_name",
                            "type": "string",
                        },
                        {
                            "name": "product_type",
                            "type": "string",
                        },
                        {
                            "name": "product_category",
                            "type": "string",
                        },
                        {
                            "name": "qty",
                            "type": "string",
                        },
                        {
                            "name": "unit",
                            "type": "string",
                        },
                        {
                            "name": "unit_price",
                            "type": "string",
                        },
                        {
                            "name": "amount_type",
                            "type": "string",
                        },
                        {
                            "name": "tax_type",
                            "type": "string",
                        },
                        {
                            "name": "tax_scope",
                            "type": "string",
                        },
                        {
                            "name": "tax_amount",
                            "type": "string",
                        },
                        {
                            "name": "Line_allowance_code",
                            "type": "string",
                        },
                        {
                            "name": "Line_allowance_reason",
                            "type": "string",
                        },
                        {
                            "name": "Line_allowance_amount",
                            "type": "string",
                        },
                        {
                            "name": "Line_charge_code",
                            "type": "string",
                        },
                        {
                            "name": "Line_charge_reason",
                            "type": "string",
                        },
                        {
                            "name": "Line_charge_amount",
                            "type": "string",
                        },
                        {
                            "name": "total_price",
                            "type": "string",
                        },
                    ],
                }

            },
        },
    ],
}
