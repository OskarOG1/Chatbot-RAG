---
url: https://help.allegro.com/en/sell/a/parameters-on-allegro-YWx9qDeO9Ib
tytul: Parameters on Allegro
agent: sprzedaz
podslug: adding-products-to-the-catalog
---



Parameters describe the product's characteristics. The more parameters you add to your offer, the more information you provide to buyers about the product you sell.
The most important parameters are the GTIN (EAN code), Brand or Manufacturer, Manufacturer code, Model.
You can complete parameters while listing an offer: in the
listing form
, through the
API
, or from a
file
. Buyers will then see them on the listing page in the
Parameters
section.
Parameters should describe the properties of a product you sell in the most complete way possible. That is why they might be different depending on the category in which you list the offer.
Why you should complete the parameters
The buyer can filter search results and more easily find the product they are interested in.
Your offer will appear higher in Google search results.
When you select a product from the Allegro Product Catalog, we automatically complete the parameters for you — thanks to this, you can reduce the time it takes to list offers.
Based on the parameters, we will automatically create a name for the product in most categories.
Learn more
.

You will receive details about the product, including its parameters, from the manufacturer or distributor of the goods. They are often listed on the packaging or in the operating instructions.

What the GTIN (EAN code) is
The GTIN (EAN code) is a unique product ID recognized worldwide. It can be 8, 12, 13, or 14 digits long. In Europe, it is usually GTIN-13, and you can find it on the product packaging below the EAN barcode.
The GTIN allows you to unambiguously identify a product. It is a market standard used by stores, retail chains, and e-commerce platforms.
How to obtain the GTIN (EAN code) — information for manufacturers
The GTIN (EAN code) is assigned by the manufacturer or brand owner.
If a product does not have a GTIN, contact the manufacturer. They should contact the
GS1 organization
(the only source of valid GTINs) to mark their products.
When a manufacturer obtains a GTIN, they must activate it — that is, enter it into the GS1 registry. The number will be present in the GS1 database only then, and it will be possible to use it to identify the product on the market.

The number will appear in the GS1 database within 24 hours of the moment it is assigned to a product. When that happens, you can
add the new product to our Product Catalog
. We will then check the GS1 database to verify that the product's GTIN (EAN code) is correct. If you complete the parameters correctly and add images, we will automatically add the new product to the Product Catalog.

How to check whether the GTIN (EAN code) is correct — information for sellers
If you are a seller or distributor, and not the manufacturer of a given product, you may get the GTINs from the manufacturer, wholesale store, or another business partner. In such a case, you can check in the
GS1 database
if the GTINs are correct.
What you can check in the GS1 database:
the correctness of a GTIN (EAN code) — whether it has been issued by GS1
information about the product assigned to the number
manufacturer/brand owner details.
Key rules regarding GTINs (EAN codes)
The most important rule to follow when assigning GTINs to products is the unique identification of each product with specific parameters. The GTIN (EAN code) identifies the product, not the right to its exclusive use by the brand owner.

The GTIN is assigned permanently. The GTIN cannot be reused for any product. If a manufacturer introduces changes to a product, for example, amends its features or creates a new brand, then, from a customer's perspective, it is a different product. For that reason, the manufacturer should create a new product and assign it a new GTIN.

10 basic rules for assigning GTINs according to GS1
When you should assign or change GTIN
What is required
introduction of a new product
What is required
new GTIN for the retail product and multipack
change of the product's features, form, or functionality
What is required
new GTIN
change in net content — volume, number of units in a packaging, weight
What is required
new GTIN for the retail product and multipack
change of measurements and/or gross weight of the packaging by more than 20%
What is required
new GTIN for the retail product and multipack
addition or removal of a certification mark that is important from the perspective of regulatory authorities, partners in the supply chain, or customers
What is required
change of the GTIN for a retail product and multipack
brand change
What is required
new GTIN for the retail product and multipack
seasonal/promotional product modifications — for example, a change of a packaging in the Christmas or promotional period
What is required
change of GTIN only for the multipack
change of the multipack content — for example, change of the declared number of goods in the multipack (box, pallet)
What is required
new GTIN for the packaging
change of the assortment predefined in a set — when one of the products from the set, which can also be sold separately, changes
What is required
new GTIN for the retail product and multipack
price on the packaging — addition, deletion, or change of the price permanently printed on the packaging as the graphic element
What is required
change of the GTIN for a retail product and multipack
If you are not sure when a new GTIN is needed, use the
Decision-Support Tool from GS1
.

How to mark products in sets ―
download the file (PDF, 3.30 MB)
.
How to mark products without a trade name (brand) ―
download the file (PDF, 1.37 MB)
.

Additional hints
Brand or product changes within the same GTIN (EAN code)
According to the GS1 standards, brand change or a significant product modification requires a new GTIN (EAN code).
Reusing a GTIN for a product with a new brand may result in errors, such as a message about an incorrect GTIN (EAN code) when listing, relisting, or editing an offer. For some GTINs (EAN codes), we are blocking changes to the brand or other parameters in the existing products in the Catalog to maintain consistency with historical and sales data.
Use the original GTINs (EAN codes).
If a product already has a GTIN (EAN code) assigned by the manufacturer, use it.
Using your own GTINs (EAN codes) for branded products (when your company is not the brand owner) negatively influences the Catalog quality and makes it difficult for buyers to find your offers.
Always check whether the product you want to list has not already been added to the Catalog under the official GTIN (EAN code) of the manufacturer/brand.
If you create a set that is made of a few separate products
(for example, a camera + a memory card),
do not assign it a new single GTIN (EAN code)
— unless you are the manufacturer of this set and you have registered it in GS1.
To list an offer with such a product, use
product sets
. Thanks to that, all products that you list as a set will have the correct parameters.
How to complete the Brand/Manufacturer and Model parameters
The Brand/Manufacturer
parameter determines the brand owner or manufacturer of the product you sell. You can select a brand or manufacturer name from the drop-down list in the listing form.
The
model
is the full trade name of the product given by the manufacturer. Thanks to this parameter, buyers can find exactly the product variant they are looking for.

Product
: sports shoes
Brand
: Allegro
Model
: Speed Flats 1 Brand Orange
If a buyer uses the term "
Speed
" while searching for Allegro shoes, we will display different product variants — both in terms of model and color of the shoe. However, if they use the full model name — for example, "
Speed Flats 1 Brand Orange
" — we will display only one specific model and color.

How to complete the Manufacturer code parameter
Manufacturer code is a unique number that the manufacturer generates for products. It is a string of letters, numbers, and characters of a various length. You can find it on the manufacturer's website or product packaging — do not confuse it with the GTIN (EAN code). It is sometimes labeled:
Product ID
Product number
Manufacturer's catalog number
Catalog number of the part
Catalog number.
If you manufacture your own products, you can assign them the manufacturer code yourself. Such a code is standardized across the market. It will help you correctly
catalog your products
.

This is a key parameter if you want your offers to be higher in the Google search results.

The manufacturer code of the Samsung Galaxy S10e smartphone is SM-G970F/DS. You can find it:
on the manufacturer's website — usually under the product's name
on the packaging.

How the GTIN (EAN code), manufacturer code, and serial number differ
The GTIN (EAN code)
is a unique number assigned by the GS1 organization. It consists only of numbers, does not contain letters or special characters. The manufacturer uses it during its commercial activities.
The manufacturer code
is assigned by the manufacturer and is unique for a single model or variant of the product. There are no standards for this type of code, so its length and the characters used are chosen by the manufacturer. It can contain both numbers and letters. The manufacturer uses it mainly to identify the product within its range. It may happen that products from different categories will have the same manufacturer code.
The serial number
is assigned by the manufacturer to the specific units of the product. Thanks to it, he can identify which series the product comes from, where it was manufactured or serviced.
How to add parameters correctly
The parameters you complete help buyers determine if your product is right for them. If you enter incorrect information, you may mislead buyers or discourage them from purchasing. Thanks to the parameters, we know what product you sell in your offer. Based on them, you connect the offer with the Product Catalog and add a new product. That is why you should avoid providing:
incorrect values
— random characters and numbers such as xyz, zzzz, 111
vague values
that do not provide any information on the product, for example: missing, other, own
keywords
, for example: cheap, hit, discount
your
login name
.
How you can report missing values in parameters
If a given parameter does not have the value you need, you can report it to us.
Go to the
Report a missing parameter value
tab.
Provide the missing parameter value. In addition, send us all materials that justify the report, such as a photo of the package with product data.
Click [submit]. We will verify your report and inform you via email about our decision.