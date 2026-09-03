---
url: https://help.allegro.com/en/sell/a/how-the-pricing-rules-based-on-the-price-converter-work-k1wRoYkBEuK
tytul: How the pricing rules based on the Price Converter work
agent: sprzedaz
podslug: b2b-sales
---



The Price Converter is a pricing rule that updates the offer price in the selected foreign marketplace based on:
the offer price in your registration marketplace
exchange rate information published by the European Central Bank.
That way, you can keep your pricing policy consistent in all the marketplaces, as well as react to changes in exchange rates.

Price rules based on the Price Converter allow you to manage offer prices
in the foreign marketplaces
. You cannot use that rule to manage prices in your registration marketplace.

How the Price Converter works
It converts the prices you enter in the currency of your registration marketplace into different currencies with the following formula:
the price in the currency of your registration marketplace x exchange rate = the price in the currency of a given marketplace
When converting the prices,
we round the result
— so that the final prices align with standard market practices and denominations in use for a given currency.

When you convert the price to:
We mathematically round the result to:
Examples:
Czech koruna (CZK)
We mathematically round the result to:
the full koruna — 0 decimal places
Examples:
15.09 CZK → 15 CZK
345.5391 CZK → 346 CZK
euro (EUR)
We mathematically round the result to:
the full eurocent — 2 decimal places
Examples:
1.2993 EUR → 1.30 EUR
90.3298 EUR → 90.33 EUR
Polish zloty (PLN)
We mathematically round the result to:
the full grosz — 2 decimal places
Examples:
2,437.9841 PLN → 2,437.98 PLN
156.5012 PLN → 156.50 PLN
We round
Hungarian forints (HUF)
according to different, more specific rules — depending on the amount directly resulting from the currency conversion. Check them in the table below.
When the amount converted to HUF from another currency is:
After conversion, we will round this amount to:
Examples:
2.50–7.49 HUF
After conversion, we will round this amount to:
5 HUF
Examples:
2.55 HUF → 5 HUF
6.8924 HUF → 5 HUF
7.50–9,99 HUF
After conversion, we will round this amount to:
10 HUF
Examples:
8.12 HUF → 10 HUF
9.9823 HUF → 10 HUF
over 10 HUF, and after mathematical rounding its unit place digit is 0, 1, or 2
After conversion, we will round this amount to:
multiples of 10 HUF
Examples:
10.41 HUF → 10 HUF
83,412.3311 HUF → 83,410 HUF
over 10 HUF, and after mathematical rounding its unit place digit is 3, 4, 5, 6, or 7
After conversion, we will round this amount to:
multiples of 5 HUF
Examples:
1,912.74 HUF → 1,915 HUF
20,017.3492 HUF → 20,015 HUF
over 10 HUF, and after mathematical rounding its unit place digit is 8 or 9
After conversion, we will round this amount to:
multiples of 10 HUF
Examples:
917.95 HUF → 920 HUF
3,209.1125 HUF → 3,210 HUF
If you get an amount lower than 2.50 HUF after the conversion from another currency — you will not share such an offer on allegro.hu. The minimum product price in that marketplace is
5 HUF
.

If you create your own pricing rule based on the Price Converter, we can also add or deduct a specified price percentage or a specified amount to or from the price before its conversion.
For example, if you create a rule that adds 5%, we will convert the price with the following formula:
(the price in the currency of your registration marketplace + 5% of the price in the currency of the registration marketplace) x exchange rate = the price in the currency of a given marketplace

You list an offer for
15 PLN
and share it on allegro.sk.
For the allegro.sk marketplace, you set the price rule that:
adds 10%
to the price in PLN
uses the
Price Converter
to convert the price to EUR at the current exchange rate.
To set the price for the Slovak marketplace, firstly, we will add 10% to the price in PLN — that gives 16.50 PLN.
The exchange rate applicable for the Price Converter on that day is 1 PLN = 0.231 EUR. That is why, your offer price converted for allegro.sk will be
3.81 EUR
.
A few days later, you reduce the price in PLN in the same offer to
14 PLN
.
Then, we will apply your rule to update the price in EUR. When we add 10% to the new price in PLN, we will get 15.40 PLN — then, we will convert that amount based on the current exchange rate (1 PLN = 0.246 EUR). The new price on allegro.sk will be
3.79 EUR
.

When we will update prices in offers with that rule
The Price Converter does not update prices automatically with every change in the exchange rate
. You decide when to convert prices in your offers.
When you pin the pricing rule based on the Price Converter to the offer, we will update its price in the foreign marketplace for the first time. From that moment, we will update the price each time you:
change the offer price in your registration marketplace
click [convert prices] in the
My Assortment
tab
relist the offer
— if it has expired
edit the pricing rule pinned to that offer — if you use your own pricing rule.

If you want to have the prices in your offers automatically converted — use the
Automatic Price Converter
.

How to convert prices with one click
Open
My Assortment
and go to the
Markets
tab.
At the bottom, you can see a section with information on up-to-date currency rates and the price conversion option in all offers with the Price Converter enabled.
Click [convert prices].
Done! In every offer, we will convert the price you entered in the currency of your registration marketplace into the currency of the marketplaces where you share your offers.
It may take up to several hours
.
That way, you can only convert prices in the
active
offers.
If you want to convert prices in offers with the statuses
active
,
draft
,
scheduled
or
expired
— do it in bulk:
Go to the
My Assortment
tab.
Select the offers whose prices you want to convert.
Go to the green bar at the bottom of the page, select [sales policy], and then [price].
In the window we will display, select the Price Converter pricing rule or the name of your own rule of similar type.
Click [save changes].
In every offer, we will convert the price you entered in PLN into the currency of the marketplaces where you share your offers.
It may take up to several hours
.
What the Automatic Price Converter is
You can only use the Automatic Price Converter within the
Professional or Expert Subscription
. You can enable and disable that option at will in the
Automatic Pricing
tab.
How the Automatic Price Converter works
If the currency exchange rate changes by at least 1%
in relation to the last bulk update of prices
— we will automatically adjust the price in the currency of that foreign marketplace in all offers with the
Price Converter
enabled, including all offers:
where you set your own rule based on the Price Converter
where you enabled the Price Converter while sharing the offer in the foreign marketplaces.
We will also convert the prices in the offers with the Price Converter enabled when you:
change the price in your registration marketplace
relist the offer — if it has expired
edit the pricing rule pinned to that offer — if you use your own pricing rule.

To make the Automatic Price Converter work, you need to convert prices in bulk in a given marketplace at least once. In the
My Assortment
tab, click [convert prices].

What the last bulk update of prices is
It is the moment when we last updated prices in the offers:
when you used the [convert prices] option in the
My Assortment
tab
or
automatically, because the currency exchange rate changed by at least 1% in relation to the last bulk update.
When we will convert prices
Each time the reference exchange rate, announced by the European Central Bank on the day before the day of the currency conversion, changes by at least 1% in relation to the last bulk update.
Additional information
Similarly to
other pricing rules
, the Price Converter
will not work in offers currently participating in campaigns or programs
that directly impact their prices. Examples of such campaigns and programs include AlleDiscount, Allegro Prices, and Smart! Week. When the campaign in which your offer participates ends, we will start applying the selected pricing rule again.
When you use the Price Converter in an offer but decide to set
your price in the currency of another marketplace
— we automatically disable the Price Converter in that offer.