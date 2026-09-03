---
url: https://help.allegro.com/en/sell/a/canceling-orders-information-for-sellers-oAd1mEk66uZ
tytul: Canceling orders ― information for sellers
agent: sprzedaz
podslug: subscription-benefits
---



If a buyer makes a mistake while placing an order, they can cancel it in the
Purchase history
tab. In some cases we may cancel your order automatically.
When a buyer can cancel their purchase
An order can be canceled only by customers purchasing from a regular account who do not want to receive from you an invoice issued with their business details. Buyers can only cancel purchases from offers listed from a
business account
.
The buyer can cancel their order until you provide them with the tracking number or you change the order status into one of the following:
in progress
ready for dispatch
dispatched
awaiting pick-up
delivered.
Learn how to change the order status
in the Orders tab
.
Orders you have not started handling yet can be canceled by the buyer
within 3 days of the day of purchase
.

Buyers from foreign marketplaces (allegro.cz, allegro.sk, allegro.hu) can cancel their order
within 5 minutes of the purchase
— even if you add the tracking number or change the order status to one of the mentioned above.

If the buyer does not see the
Cancel purchase
option, it does not mean they lose their
rights as a consumer
. They can still withdraw from the agreement without giving a reason and use the
Return purchase
option.

When we will cancel your order automatically
We automatically cancel an order if the buyer chooses the payment in advance and fails to pay for their order on time. The deadline is:
7 days ― in the case of purchases made with the buy now option or in an auction, with a payment option
other than a standard transfer
14 days ― in the case of purchases made with the buy now option, with payment in advance with a
standard transfer
.
You can decide after what time we cancel an order
You can set
your own
deadline to pay for purchases after which we will cancel an unpaid order in the Orders tab:
you can do so
only for the buy now offers and auctions
the deadline you set
cannot be shorter than 7 days, nor longer than 30 days
.
After the automatic order cancelation, we will send you and the buyer an email informing you which order has been canceled.
Automatic order cancellation is possible for all sellers’ offers on Allegro ― listed on both business and regular accounts. You cannot disable automatic cancellation of unpaid orders.
What if you do not have the product you offer and want to cancel the purchase
As a seller, you are obliged to fulfill a distance agreement concluded with a buyer. However, if for any reason you do not have the product that your customer bought in one of your offers:
contact the buyer and offer a solution
get hold of the missing product and send the order to the buyer.
Update your stocks to avoid such situations.

Only the buyer has the right to withdraw from a distance agreement. If the buyer does not withdraw from the agreement and you change the order status to
Canceled
— this does not terminate the distance agreement with the buyer.

In what categories buyers cannot cancel their order
Medications
― we do not automatically cancel purchases in this category
Investment Products
― for example gold
Gift Cards
Codes and Vouchers
Online games
Audiobooks
E-books
.
Orders with digital delivery cannot be canceled either ― regardless of the category the item was listed in.
Canceled purchase in API
If you use API, you can find information about the cancellation in the event log ―
GET /order/events
:
BUYER_CANCELLED ― means that the buyer has canceled their order
AUTO_CANCELLED ― means that we have canceled the order automatically due to lack of payment.
The buyer can cancel their order as long as you do not change their order status to one of the following:
PROCESSING
READY_FOR_SHIPMENT
SENT
READY_FOR_PICKUP
PICKED_UP
This is why you should always change the order status once you start processing orders.
Order fulfillment status change in API
You can change an order fulfillment status visible in the
fulfillment.status
field via
PUT /order/checkout-forms/{checkoutForm.id}/fulfillment
. As checkoutForm.id provide us with the order number you will get in response to
GET /order/checkout-forms
.
Learn more about
order fulfillment status change in API
.
The buyer canceled a paid order
Refund the buyer via
POST /payments/refunds
.
Learn more about
order cancellation in API
.
How to process a canceled order
When a buyer cancels their order, we will inform you about it by email and display such information next to the order.
When a customer
cancels a purchase they paid for
, we will make an automatic refund attempt — from the funds you see in the
Funds and Operations History
tab. If your balance does not contain sufficient funds for an automatic refund, we will attempt to collect the money over the
next 2 working days
.

Foreign marketplaces
: we will create an automatic
refund request within Allegro Buyer Protection
on behalf of the registered customer and issue the refund within the program. Next, we will add the refund amount to your remaining Allegro service fees — you will find it in the
Settlements with Allegro
tab.
allegro.pl
: the customer can open a Discussion with you. If you do not reach an agreement — the customer will be able to submit a request for a refund from Allegro Buyer Protection.

A transaction rebate (sales commission refund) for canceled orders
You will receive a
transaction rebate (sales commission refund) without applying for it
for a canceled order if:
a buyer cancels their unpaid order ― it concerns both buy now offers and auctions
a buyer cancels their paid order and we refund them automatically
we cancel an order automatically when a customer fails to meet the payment deadline ― it concerns only buy now offers.
A transaction rebate (sales commission refund) for auctions canceled automatically
If we cancel an order automatically in an auction, you need to
apply
for a transaction rebate (sales commission refund)
.
What buyers cannot do once their order is canceled
No matter whether the order was canceled by the buyer or us, after the cancellation the customer cannot:
pay for this purchase
rate you for this transaction.