catalogue_quotation_schema = {
    "type": "record",
    "name": "CatalogueQuotation",
    "fields": [{
        "name": "Catalogue_Quotation_Ref",
        "type": [{
            "type": "record",
            "name": "Catalogue_Quotation_Ref",
            "fields": [{
                "name": "Catalogue_Quotation_Reference",
                "type": "string"
            }, {
                "name": "Catalogue_Request_Reference",
                "type": "string"
            }, {
                "name": "RFC_Reference",
                "type": "string"
            }]
        }]
    }, {
        "name": "Catalogue_Products",
        "type": [{
            "type": "array",
            "items": [{
                "type": "record",
                "name": "Catalogue_Product",
                "fields": [{
                    "name": "Product_Barcode",
                    "type": "string"
                }, {
                    "name": "Product_Default_Code",
                    "type": "string"
                }, {
                    "name": "Product_Lead_Time",
                    "type": "string"

                }, {
                    "name": "Product_Name",
                    "type": "string"

                }, {
                    "name": "Product_Type",
                    "type": "string"

                },{
                    "name": "Product_Price",
                    "type": "string"

                }, {
                    "name": "Product_UoM",
                    "type": "string"

                }, {
                    "name": "Product_Variants_Desc",
                    "type": "string"

                }, {
                    "name": "Product_Volume",
                    "type": "string"

                }, {
                    "name": "Product_Weight",
                    "type": "string"

                }, {
                    "name": "Product_With_Variant",
                    "type": "string"

                }]
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
