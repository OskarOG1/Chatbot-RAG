---
url: https://help.allegro.com/en/sell/a/product-search-engine-what-it-is-and-how-it-works-8dvWq0KZBuO
tytul: Product search engine — what it is and how it works
agent: sprzedaz
podslug: linking-offers-to-the-catalog
---



How to use the product search engine
Go to the
listing form
. Enter the GTIN (EAN) in the search bar, and click [search]. Based on that, we will scan the Allegro Product Catalog to find matching products.

If you cannot provide the code, select
My product does not have a GTIN (EAN) code
. We will then ask you to enter the product name.

If we find the matching products, we will display their list. You can filter products on the list by category and parameters. If you click on a given product, we will display its details.

If the product list is too long or you want to list your offer in a specific category, use the category list on the left.

Check whether the product you want to sell is on the list. If not ― you can click [continue without selecting a product]. We will try to create a new product based on the information you provide in the listing form.
Learn more
.
Once you select the product, click it. We will display the details — a set of parameters like, for example, color — that describe the selected product. The parameters will help you decide whether you have found the right product.

We want the products available in the Catalog to be top quality. If you spot an error in the product details ―
report it
instead of correcting it only in the listing form. Click [report incorrect product information] on the product card.

If the product parameters are correct and you want to list an offer based on them, click [select].
What if you only want to use the search engine without listing any offers? In that case, click
this link
.
If you use the Allegro API
To find a product in the Allegro Product Catalog, use the
GET/sale/products
resource.
Learn more
.
If you know the GTIN (EAN) or the product ID, provide it in the
product.id
field, in the
POST/sale/product-offers
request structure. In that case, you will only use the product from our Catalog.
We will not create a new product
, even if you provide all the necessary details.
Do not complete the
product.id
field if you want to add a new product to the Catalog. Provide the GTIN (EAN) and other details in the
product.parameters
field.
Learn more
.
Frequently asked questions

The product in that offer may be incomplete — it may not contain all the details required for that type of assortment. In that case, contact us
using the form
.

First, check if you have searched for the correct product variant. For example, if you are searching for iPhone 11, there are already several model versions. In that case, select the proper variant first.
If you are sure that the parameters are incorrect, click [report incorrect product information].
Learn more
.

Remember that the category in which you want to list your cataloged offer and the product category have to match. If you want to change that category, you can select another one — from the set of similar categories. Check
how it works
.
If you think that the product category is incorrect, you can
suggest its change
.