invoice_acknowledgement_schema = {
    "type": 'record',
    "name": 'invoice_acknowledgement',
    "fields": [
        {
            "name": 'AckDt',
            "type": 'string',
        },
        {
            "name": 'AckNo',
            "type": 'string',
        },
        {
            "name": 'IRN',
            "type": 'string',
        },
        {
            "name": 'Created_by',
            "type": 'string'
        },
        {
            "name": 'Created_Date',
            "type": 'string'
        },
        {
            "name": 'Signed_invoice',
            "type": 'string',
        },
        {
            "name": 'Signed_QRCode',
            "type": 'string',
        },
        {
            "name": 'Inv_Status',
            "type": 'string',
        },
    ]
}
