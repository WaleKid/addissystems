/** @odoo-module **/

import { Component, markup } from "@odoo/owl";
import { isMacOS } from "@web/core/browser/feature_detection";
import { escape } from "@web/core/utils/strings";
import { session } from "@web/session";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";

function documentationItem(env) {
    const documentationURL = "https://addissystems.et/documentation";
    return {
        type: "item",
        id: "documentation",
        description: env._t("Documentation"),
        href: documentationURL,
        callback: () => {
            browser.open(documentationURL, "_blank");
        },
        sequence: 10,
    };
}

function supportItem(env) {
    const url = "https://addissystems.et/support";
    return {
        type: "item",
        id: "support",
        description: env._t("Support"),
        href: url,
        callback: () => {
            browser.open(url, "_blank");
        },
        sequence: 20,
    };
}


function odooAccountItem(env) {
    const addis_systems_URL = "https://addissystems.et/account";
    return {
        type: "item",
        id: "account",
        description: env._t("Addis Systems account"),
        callback: () => {
            browser.open(addis_systems_URL, "_blank");
        },
        sequence: 60,
    };
}


registry
    .category("user_menuitems")
    .remove("documentation", documentationItem)

registry
    .category("user_menuitems")
    .remove("support", supportItem)

registry
    .category("user_menuitems")
    .remove("odoo_account", odooAccountItem)

registry
    .category("user_menuitems")
    .add("documentation", documentationItem)
    .add("support", supportItem)
    .add("odoo_account", odooAccountItem)
