Tryton Avatax Integration
=========================

This module integrates Tryton Sale and Account modules with the Avatax Tax
calc API and creates taxes on the fly.

Why AvaTax Integration ? Why not use Tryton tax rules
-----------------------------------------------------

Tryton tax rules are powerful but the US supposedly has 11,000 tax 
jurisdictions and keeping the system updated with all the rules could
easily end up being a full time job and a pain in the rear!

However, if your business has only one location, this would be simpler and
Tryton tax rules could work in most cases. One exception to this is the
`Tax Holiday <http://en.wikipedia.org/wiki/Tax_holiday>`_ system in the
United States, where there are temporary reductions or elimination of taxes
for a certain period in a year.

Configuration
-------------

The Avatax integration can be enabled or disabled for each company.
Checking the `Enable Avatax` boolean field on the company activates Avatax
tax computation for you.

Setting Up
``````````

The following information is required to start using the integration with
Avatax:

* License Key: This is the license key that needs to be set in the 
  credentials portion of your connector (this is **not** an Admin Console
  Password)
* URL: The URL for the development service is 
  https://development.avalara.net. If you are connecting to the production
  service, the URL is https://rest.avalara.net.
* Company Code: The code of the company that you have setup on the admin
  console.

How does it work ?
------------------

When the sale order is coverted from `Draft` state to the `Quotation` state
the taxes are looked up and the taxes are added to each line. If a tax
with the given rate and type does not exist, it is created on the fly.


Dependencies
------------

This module depends on the 
`Python API for Avatax <https://github.com/openlabs/Avatax>`_ written by
`Openlabs <http://openlabs.co.in>`_. 


Support
-------

Commercial support on the module is available from 
`Openlabs <http://openlabs.co.in>`_.
