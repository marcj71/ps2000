# ps2000

This is a python 3 class to control [EA](http://www.elektroautomatik.de/) power supplies of the PS2000 series. The series includes the following types:

- [EA-PS 2042-06B](http://shop.elektroautomatik.de/shop/shop__LABORNETZGER%C3%84T%200...42V0...6A100W__1::4::14::42::a39200112__en_US)
- [EA-PS 2042-10B](http://shop.elektroautomatik.de/shop/shop__LABORNETZGER%C3%84T%200...42V0..10A160W__1::4::14::42::a39200113__en_US)
- [EA-PS 2042-20B](http://shop.elektroautomatik.de/shop/shop__LABORNETZGER%C3%84T%200...42V0..20A320W__1::4::14::42::a39200114__en_US)
- [EA-PS 2084-03B](http://shop.elektroautomatik.de/shop/shop__LABORNETZGER%C3%84T%200...84V0...3A100W__1::4::14::42::a39200116__en_US)
- [EA-PS 2084-05B](http://shop.elektroautomatik.de/shop/shop__LABORNETZGER%C3%84T%200...84V0...5A160W__1::4::14::42::a39200117__en_US)
- [EA-PS 2084-10B](http://shop.elektroautomatik.de/shop/shop__LABORNETZGER%C3%84T%200..84V0..10A320W__1::4::14::42::a39200118__en_US)

So far, it has only been tested with the EA-PS 2042-20B. Running ps2000.py by itself will show the capabilities. Include the class in your own scripts using `import ps2000`.

It's trivial to expand the code to support multiple-output power supplies of the PS 23xx range, if you need it. Also, automatic port selection would be nice.
