// Window/script references
const currentUrl = window.location.href;
const currentScript = document.currentScript;

// CSRF token
const csrfToken = currentScript.getAttribute("data-csrf-token");

// Order data
const paymentAmount = currentScript.getAttribute("data-payment-amount");
const wfOrderId = currentScript.getAttribute("data-wf-order-id");

// URLs
const orderCreateUrl = currentScript.getAttribute(
  "data-paypal-order-create-url",
);
const orderCaptureUrl = currentScript.getAttribute(
  "data-paypal-order-capture-url",
);
const paymentDoneUrl = currentScript.getAttribute("data-payment-done-url");

const FUNDING_SOURCES = [
  paypal.FUNDING.PAYPAL,
  // paypal.FUNDING.CARD,
];

FUNDING_SOURCES.forEach((fundingSource) => {
  paypal
    .Buttons({
      fundingSource,
      style: {
        layout: "vertical",
        shape: "pill",
        color: fundingSource == paypal.FUNDING.PAYLATER ? "gold" : "",
      },
      createOrder: async (data, actions) => {
        // This function sets up the details of the transaction,
        // including the amount and line item details.
        const paypalOrderId = await fetch(orderCreateUrl, {
          method: "post",
          headers: {
            "content-type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            wf_order_id: wfOrderId,
          }),
        })
          .then((response) => {
            return response.json();
          })
          .then((orderData) => {
            return orderData.paypal_order_id;
          });

        return paypalOrderId;
      },
      onApprove: async (data, actions) => {
        // This data comes from PayPal's servers
        // with the following information:
        // {
        //   orderID: string;
        //   payerID: string;
        //   paymentID: string;
        //   billingToken: string;
        //   facilitatorAccessToken: string;
        // }

        payload = {
          paypal_order_id: data.orderID,
          paypal_payment_id: data.paymentID,
        };

        // Capture the funds from the transaction
        result = await fetch(orderCaptureUrl, {
          method: "post",
          headers: {
            "content-type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify(payload),
        });

        if (result.status === 201) {
          // Show a success page to the buyer
          window.location.href = paymentDoneUrl;
        } else {
          console.log("error");
          console.log(result.status);
          console.log(result.statusText);
          console.log(result.body);
        }
      },
      onCancel: async (data, actions) => {
        // Show a cancel page, or return to cart
        // This URL is safely generated on the server side
        // and does not require HTML decoding.
        // lgtm[js/xss-through-dom]
        window.location.href = currentUrl;
      },
      onError: async (err) => {
        // Show an error page here, when an error occurs
        console.log(err);
      },
    })
    .render("#paypal-button-container");
});
