log_tracking_schema = {
    "type": "record",
    "name": "InvoiceLogStatus",
    "fields": [
        {
            "name": "InvoiceID",
            "type": "string"
        },
        {
            "name": "InvoiceCreatedDate",
            "type": "string"
        },
        {
            "name": "CompanyName",
            "type": "string"
        },
        {
            "name": "ErrorStatus",
            "type": {
                "type": "record",
                "name": "errorStatus",
                "fields": [
                    {
                        "name": "sentStatus",
                        "type": {
                            "type": "record",
                            "name": "sent",
                            "fields": [
                                {
                                    "name": "Sent_INV",
                                    "type": "string"
                                },
                                {
                                    "name": "Sent_INV_AT",
                                    "type": "string"
                                }
                            ]
                        },
                    },
                    {
                        "name": "received_Status",
                        "type": {
                            "type": "record",
                            "name": "received_cons",
                            "fields": [
                                {
                                    "name": "Received_INV",
                                    "type": "string"
                                },
                                {
                                    "name": "Received_INV_AT",
                                    "type": "string"
                                }
                            ]
                        },
                    },
                    {
                        "name": "Ack_gen_Status",
                        "type": {
                            "type": "record",
                            "name": "Ack_gen_cons",
                            "fields": [
                                {
                                    "name": "Ack_Gen_INV",
                                    "type": "string"
                                },
                                {
                                    "name": "Ack_Gen_INV_AT",
                                    "type": "string"
                                }
                            ]
                        },
                    },
                    {
                        "name": "Ack_save_Status",
                        "type": {
                            "type": "record",
                            "name": "Ack_save_cons",
                            "fields": [
                                {
                                    "name": "Ack_Save_INV",
                                    "type": "string"
                                },
                                {
                                    "name": "Ack_Save_INV_AT",
                                    "type": "string"
                                }
                            ]
                        },
                    },
                    {
                        "name": "Ack_Sent_Status",
                        "type": {
                            "type": "record",
                            "name": "Ack_Sent_cons",
                            "fields": [
                                {
                                    "name": "Ack_Sent_INV",
                                    "type": "string"
                                },
                                {
                                    "name": "Ack_Sent_INV_AT",
                                    "type": "string"
                                }
                            ]
                        },
                    },
                    {
                        "name": "Ack_Consume_Status",
                        "type": {
                            "type": "record",
                            "name": "Ack_Consume_cons",
                            "fields": [
                                {
                                    "name": "Ack_Consume_INV",
                                    "type": "string"
                                },
                                {
                                    "name": "Ack_Consume_INV_AT",
                                    "type": "string"
                                }
                            ]
                        },
                    },
                    {
                        "name": "Ack_Exchange",
                        "type": {
                            "type": "record",
                            "name": "Ack_Exchange_pro",
                            "fields": [
                                {
                                    "name": "Ack_Exchange_INV",
                                    "type": "string"
                                },
                                {
                                    "name": "Ack_Exchange_INV_AT",
                                    "type": "string"
                                }
                            ]
                        },
                    },
                    {
                        "name": "Ack_Exchange_Cons",
                        "type": {
                            "type": "record",
                            "name": "Ack_Exchange_cons",
                            "fields": [
                                {
                                    "name": "Ack_Exchange_Cons_INV",
                                    "type": "string"
                                },
                                {
                                    "name": "Ack_Exchange_Cons_INV_AT",
                                    "type": "string"
                                }
                            ]
                        },
                    },
                    {
                        "name": "Ack_Send_To_Vendor",
                        "type": {
                            "type": "record",
                            "name": "Ack_Send_ToVendor",
                            "fields": [
                                {
                                    "name": "Ack_Send_To_Vendor_INV",
                                    "type": "string"
                                },
                                {
                                    "name": "Ack_Send_To_Vendor_INV_AT",
                                    "type": "string"
                                }
                            ]
                        },
                    },
                    {
                        "name": "Ack_Verify_Status",
                        "type": {
                            "type": "record",
                            "name": "Ack_Verify_cons",
                            "fields": [
                                {
                                    "name": "Ack_Verify_INV",
                                    "type": "string"
                                },
                                {
                                    "name": "Ack_Verify_INV_AT",
                                    "type": "string"
                                }
                            ]
                        },
                    },
                    {
                        "name": "Ack_StatusUpdate_Status",
                        "type": {
                            "type": "record",
                            "name": "Ack_StatusUpdate_cons",
                            "fields": [
                                {
                                    "name": "Ack_StatusUpdate_INV",
                                    "type": "string"
                                },
                                {
                                    "name": "Ack_StatusUpdate_INV_AT",
                                    "type": "string"
                                }
                            ]
                        },
                    },
                ]
            }
        },
        {
            "name": "ErrorResponse",
            "type": "string",
        }
    ]
}
