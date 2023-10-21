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
  "data-paypal-order-create-url"
);
const orderCaptureUrl = currentScript.getAttribute(
  "data-paypal-order-capture-url"
);
const paymentDoneUrl = currentScript.getAttribute(
  "data-payment-done-url"
);

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
        return fetch(orderCreateUrl, {
          method: "post",
          headers: {
            "content-type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            wf_order_id: wfOrderId,
          }),
        })
        .then((res) => {
          return res.json();
        })
        .then((orderData) => {
          return orderData.id;
        });
      },
      onApprove: async (data, actions) => {
        result = await fetch(orderCaptureUrl, {
          method: "post",
          headers: {
            "content-type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            paypalOrderId: data.orderID,
          }),
        });

        if (result.status === 201) {
          window.location.href = encodeURIComponent(paymentDoneUrl);
        } else {
          console.log("error");
          console.log(result.status);
          console.log(result.statusText);
          console.log(result.body);
        }
      },
      onCancel: async (data, actions) => {
        // Show a cancel page, or return to cart
        window.location.href = currentUrl;
      },
      onError: async (err) => {
        // Show an error page here, when an error occurs
        console.log(err);
      },
    })
    .render("#paypal-button-container");
});
