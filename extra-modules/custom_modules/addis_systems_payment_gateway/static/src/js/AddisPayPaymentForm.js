/* global AddispayCheckout */
odoo.define('payment_addis_pay.payment_form', require => {
    'use strict';

    const core = require('web.core');
    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');

    const _t = core._t;

    const addispayMixin = {

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Handle the additional details event of the Addis Pay drop-in.
         *
         * @private
         * @param {object} state - The state of the drop-in
         * @param {object} dropin - The drop-in
         * @return {Promise}
         */
        _dropinOnAdditionalDetails: function (state, dropin) {
            return this._rpc({
                route: '/payment/addispay/payment_details',
                params: {
                    'provider_id': dropin.providerId,
                    'reference': this.addispayDropin.reference,
                    'payment_details': state.data,
                },
            }).then(paymentDetails => {
                if (paymentDetails.action) { // Additional action required from the shopper
                    dropin.handleAction(paymentDetails.action);
                } else { // The payment reached a final state, redirect to the status page
                    window.location = '/payment/status';
                }
            }).guardedCatch((error) => {
                error.event.preventDefault();
                this._displayError(
                    _t("Server Error"),
                    _t("We are not able to process your payment."),
                    error.message.data.message
                );
            });
        },

        /**
         * Handle the error event of the Addis Pay drop-in.
         *
         * @private
         * @param {object} error - The error in the drop-in
         * @return {undefined}
         */
        _dropinOnError: function (error) {
            this._displayError(
                _t("Incorrect Payment Details"),
                _t("Please verify your payment details.")
            );
        },

        /**
         * Handle the submit event of the Addis Pay drop-in and initiate the payment.
         *
         * @private
         * @param {object} state - The state of the drop-in
         * @param {object} dropin - The drop-in
         * @return {Promise}
         */
        _dropinOnSubmit: function (state, dropin) {
            // Create the transaction and retrieve the processing values
            return this._rpc({
                route: this.txContext.transactionRoute,
                params: this._prepareTransactionRouteParams('addispay', dropin.providerId, 'direct'),
            }).then(processingValues => {
                this.addispayDropin.reference = processingValues.reference; // Store final reference
                // Initiate the payment
                return this._rpc({
                    route: '/payment/addispay/payments',
                    params: {
                        'provider_id': dropin.providerId,
                        'reference': processingValues.reference,
                        'converted_amount': processingValues.converted_amount,
                        'currency_id': processingValues.currency_id,
                        'partner_id': processingValues.partner_id,
                        'payment_method': state.data.paymentMethod,
                        'access_token': processingValues.access_token,
                        'browser_info': state.data.browserInfo,
                    },
                });
            }).then(paymentResponse => {
                if (paymentResponse.action) { // Additional action required from the shopper
                    this._hideInputs(); // Only the inputs of the inline form should be used
                    $('body').unblock(); // The page is blocked at this point, unblock it
                    dropin.handleAction(paymentResponse.action);
                } else { // The payment reached a final state, redirect to the status page
                    window.location = '/payment/status';
                }
            }).guardedCatch((error) => {
                error.event.preventDefault();
                this._displayError(
                    _t("Server Error"),
                    _t("We are not able to process your payment."),
                    error.message.data.message
                );
            });
        },

        /**
         * Prepare the inline form of Adyen for direct payment.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {string} code - The code of the selected payment option's provider
         * @param {number} paymentOptionId - The id of the selected payment option
         * @param {string} flow - The online payment flow of the selected payment option
         * @return {Promise}
         */
        _prepareInlineForm: function (code, paymentOptionId, flow) {
            if (code !== 'addispay') {
                return this._super(...arguments);
            }

            // Check if instantiation of the drop-in is needed
            if (flow === 'token') {
                return Promise.resolve(); // No drop-in for tokens
            } else if (this.addispayDropin && this.addispayDropin.providerId === paymentOptionId) {
                this._setPaymentFlow('direct'); // Overwrite the flow even if no re-instantiation
                return Promise.resolve(); // Don't re-instantiate if already done for this provider
            }

            // Overwrite the flow of the select payment option
            this._setPaymentFlow('direct');

            // Get public information on the provider (state, client_key)
            return this._rpc({
                route: '/payment/addispay/provider_info',
                params: {
                    'provider_id': paymentOptionId,
                },
            }).then(providerInfo => {
                // Get the available payment methods
                return this._rpc({
                    route: '/payment/addispay/payment_methods',
                    params: {
                        'provider_id': paymentOptionId,
                        'partner_id': parseInt(this.txContext.partnerId),
                        'amount': this.txContext.amount
                            ? parseFloat(this.txContext.amount)
                            : undefined,
                        'currency_id': this.txContext.currencyId
                            ? parseInt(this.txContext.currencyId)
                            : undefined,
                    },
                }).then(paymentMethodsResult => {
                    // Instantiate the drop-in
                    const configuration = {
                        paymentMethodsResponse: paymentMethodsResult,
                        clientKey: providerInfo.client_key,
                        locale: (this._getContext().lang || 'en-US').replace('_', '-'),
                        environment: providerInfo.state === 'enabled' ? 'live' : 'test',
                        onAdditionalDetails: this._dropinOnAdditionalDetails.bind(this),
                        onError: this._dropinOnError.bind(this),
                        onSubmit: this._dropinOnSubmit.bind(this),
                    };
                    const checkout = new AddispayCheckout(configuration);
                    this.addispayDropin = checkout.create(
                        'dropin', {
                            openFirstPaymentMethod: true,
                            openFirstStoredPaymentMethod: false,
                            showStoredPaymentMethods: false,
                            showPaymentMethods: true,
                            showPayButton: false,
                            setStatusAutomatically: true,
                        },
                    ).mount(`#o_addispay_dropin_container_${paymentOptionId}`);
                    this.addispayDropin.providerId = paymentOptionId;
                });
            }).guardedCatch((error) => {
                error.event.preventDefault();
                this._displayError(
                    _t("Server Error"),
                    _t("An error occurred when displayed this payment form."),
                    error.message.data.message
                );
            });
        },

        /**
         * Trigger the payment processing by submitting the drop-in.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {string} provider - The provider of the payment option's provider
         * @param {number} paymentOptionId - The id of the payment option handling the transaction
         * @param {string} flow - The online payment flow of the transaction
         * @return {Promise}
         */
        async _processPayment(provider, paymentOptionId, flow) {
            if (provider !== 'addispay' || flow === 'token') {
                return this._super(...arguments); // Tokens are handled by the generic flow
            }
            if (this.addispayDropin === undefined) { // The drop-in has not been properly instantiated
                this._displayError(
                    _t("Server Error"), _t("We are not able to process your payment.")
                );
            } else {
                return await this.addispayDropin.submit();
            }
        },

    };

    checkoutForm.include(addispayMixin);
    manageForm.include(addispayMixin);
});
