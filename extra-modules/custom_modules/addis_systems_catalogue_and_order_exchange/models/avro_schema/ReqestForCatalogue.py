rfc_schema = {
    "type": "record",
    "name": "RequestForCatalogue",
    "fields": [{
        "name": "Request_For_Catalogue_Ref",
        "type": [{
            "type": "record",
            "name": "Request_For_Catalogue_Ref",
            "fields": [{
                "name": "RFC_Reference",
                "type": "string"

            }, {
                "name": "pass_to_prospective_customer",
                "type": "string"
            },
                {
                    "name": "with_Price",
                    "type": "string"
                }
            ]
        }]
    }, {
        "name": "Request_For_Catalogue_Desc",
        "type": [{
            "type": "record",
            "name": "Request_For_Catalogue_Desc",
            "fields": [{
                "name": "Condition",
                "type": "string"
            }, {
                "name": "Date",
                "type": "string"

            }, {
                "name": "Descriptive_Literature",
                "type": "string"

            }, {
                "name": "Expected_Date",
                "type": "string"

            }, {
                "name": "trade_terms",
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
    }]
}
