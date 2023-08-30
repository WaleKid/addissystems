sales_order_schema = {
    "type": "record",
    "name": "SalesOrder",
    "fields": [{
        "name": "Sales_Order_ref",
        "type": [{
            "type": "record",
            "name": "Sales_Order_ref",
            "fields": [{
                "name": "PO_State",
                "type": "string"
            }, {
                "name": "RFQ_ref_no",
                "type": "string"
            }, {
                "name": "Rec_advice_ref_no",
                "type": "string"
            }, {
                "name": "SO_ref_no",
                "type": "string"
            }]
        }]
    }, {
        "name": "Sales_Order_Desc",
        "type": [{
            "type": "record",
            "name": "Sales_Order_Desc",
            "fields": [{
                "name": "Customer_Order_Ref",
                "type": "string"
            }, {
                "name": "Order_deadline",
                "type": "string"
            }, {
                "name": "Receipt_Dt",
                "type": "string"
            }, {
                "name": "SO_exchange",
                "type": "string"
            }, {
                "name": "SO_no",
                "type": "string"
            }, {
                "name": "Sales_Order_Type",
                "type": "string"
            }]
        }]
    }, {
        "name": "Seller",
        "type": [{
            "type": "record",
            "name": "Seller",
            "fields": [{
                "name": "company_name",
                "type": "string"
            }, {
                "name": "licence_number",
                "type": "string"
            }, {
                "name": "tin_no",
                "type": "string"
            }, {
                "name": "vat_reg_Dt",
                "type": "string"
            }, {
                "name": "vat_reg_no",
                "type": "string"
            }]
        }]
    }, {
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
        "type": [{
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
        "name": "Sales_total",
        "type": "string"
    }, {
        "name": "Vat_breakdown",
        "type": [{
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
    }, {
        "name": "Order_line",
        "type": [{
            "type": "array",
            "items": [{
                "type": "record",
                "name": "Order_line",
                "fields": [{
                    "name": "Line_charge_amount",
                    "type": "string"
                }, {
                    "name": "Line_charge_code",
                    "type": "string"
                }, {
                    "name": "Line_charge_reason",
                    "type": "string"
                }, {
                    "name": "hsncode",
                    "type": "string"
                }, {
                    "name": "item_name",
                    "type": "string"
                }, {
                    "name": "price",
                    "type": "string"
                }, {
                    "name": "qty",
                    "type": "string"
                }, {
                    "name": "sno",
                    "type": "string"
                }, {
                    "name": "tax",
                    "type": "string"
                }, {
                    "name": "total_price",
                    "type": "string"
                }, {
                    "name": "unit",
                    "type": "string"
                }]
            }]
        }]
    }]
}
