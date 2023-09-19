purchase_order_schema = {
    "type": "record",
    "name": "PurchaseOrder",
    "fields": [{
        "name": "Buyer",
        "type": [{
            "type": "record",
            "name": "Buyer",
            "fields": [{
                "name": "address",
                "type": "string"
            }, {
                "name": "buyer_name",
                "type": "string"
            }, {
                "name": "email",
                "type": "string"
            }, {
                "name": "location",
                "type": "string"
            }, {
                "name": "phone_no",
                "type": "string"
            }, {
                "name": "tin_no",
                "type": "string"
            }, {
                "name": "vat_reg_no",
                "type": "string"
            }]
        }]
    }, {
        "name": "Delivery_info",
        "type": ["null", {
            "type": "record",
            "name": "Delivery_info",
            "fields": [{
                "name": "Delivery_note_number",
                "type": "string"
            }, {
                "name": "delivery_address",
                "type": "string"
            }, {
                "name": "delivery_date",
                "type": "string"
            }, {
                "name": "delivery_location",
                "type": "string"
            }]
        }]
    }, {
        "name": "Purchase_Order_Desc",
        "type": ["null", {
            "type": "record",
            "name": "Purchase_Order_Desc",
            "fields": [{
                "name": "Exchange_Title",
                "type": "string"
            }, {
                "name": "Order_date",
                "type": "string"
            }, {
                "name": "Planned_Receipt",
                "type": "string"
            }, {
                "name": "Purchase_Order_Type",
                "type": "string"
            }]
        }]
    }, {
        "name": "Purchase_Order_ref",
        "type": ["null", {
            "type": "record",
            "name": "Purchase_Order_ref",
            "fields": [{
                "name": "CAT_ref_no",
                "type": "string"
            }, {
                "name": "PO_ref_no",
                "type": "string"
            }, {
                "name": "PO_status",
                "type": "string"
            }, {
                "name": "RFC_rfc_no",
                "type": "string"
            }, {
                "name": "Rec_advice_ref_no",
                "type": "string"
            }]
        }]
    }, {
        "name": "Purchase_line",
        "type": ["null", {
            "type": "array",
            "items": ["null", {
                "type": "record",
                "name": "Purchase_line",
                "fields": [{
                    "name": "HSNcode",
                    "type": "string"
                }, {
                    "name": "Line_charge_amount",
                    "type": "string"
                }, {
                    "name": "Line_charge_code",
                    "type": "string"
                }, {
                    "name": "Line_charge_reason",
                    "type": "string"
                }, {
                    "name": "Product_Description",
                    "type": "string"
                }, {
                    "name": "Product_Name",
                    "type": "string"
                }, {
                    "name": "Product_price",
                    "type": "string"
                }, {
                    "name": "Product_qty",
                    "type": "string"
                }, {
                    "name": "Product_unit",
                    "type": "string"
                }, {
                    "name": "Total_Price",
                    "type": "string"
                }, {
                    "name": "sequence",
                    "type": "string"
                }, {
                    "name": "tax_amount",
                    "type": "string"
                }, {
                    "name": "tax_amount_type",
                    "type": "string"
                }, {
                    "name": "tax_scope",
                    "type": "string"
                }, {
                    "name": "tax_type",
                    "type": "string"
                }]
            }]
        }]
    }, {
        "name": "Purchase_total",
        "type": "string"
    }, {
        "name": "Seller",
        "type": ["null", {
            "type": "record",
            "name": "Seller",
            "fields": [{
                "name": "address",
                "type": "string"
            }, {
                "name": "company_name",
                "type": "string"
            }, {
                "name": "email",
                "type": "string"
            }, {
                "name": "location",
                "type": "string"
            }, {
                "name": "phone_no",
                "type": "string"
            }, {
                "name": "tin_no",
                "type": "string"
            }, {
                "name": "vat_reg_no",
                "type": "string"
            }]
        }]
    }, {
        "name": "Vat_breakdown",
        "type": ["null", {
            "type": "record",
            "name": "Vat_breakdown",
            "fields": [{
                "name": "Vat_breakdown_amount",
                "type": "string"
            }, {
                "name": "Vat_category_code",
                "type": "string"
            }, {
                "name": "Vat_reason_code",
                "type": "string"
            }, {
                "name": "Vat_reason_text",
                "type": "string"
            }]
        }]
    }]
}
