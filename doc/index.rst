.. nvcl_kit documentation master file, created by
   sphinx-quickstart on Sat Nov 23 07:37:56 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

nvcl-kit
========

**nvcl-kit** is a Python package that provides access to Australia's National Virtual Core Library (NVCL).
This is a national database of drill cores that have been analysed by the CSIRO-developed HyLogger
hyperspectral core-scanning system. The Hylogger system uses visible and near-infrared, shortwave and thermal
infrared reflectance spectroscopy and automatic mineralogical analysis to extract mineralogy data from each
drill core.

The mineralogy data is maintained by Australia's State and Territory geological surveys and can be accessed
via publicly available web services. **nvcl-kit** combines these services with OCG WFS borehole data to provide
a complete picture of each borehole. It is designed to shield the user from the arcane details of how to
establish connections, retrieve and combine datasets.

**nvcl-kit** has two layers of API. The first layer is designed to make it quick and easy to access the borehole
mineralogy. The second layer is for more expert users providing access to the full range of available data
products.

.. seealso::
   `National Virtual Core Library <https://research.csiro.au/nvcl/>`_
      The National Virtual Core Library (NVCL) is a project led by CSIRO and funded by AuScope. Over the past 
      10 years the project has generated a wealth of data, resources and research outputs which are publicly
      available.
   `The Spectral Geologist (TSG™) <https://research.csiro.au/thespectralgeologist/>`_
      The industry standard tool for the mineralogical analysis VIS/NIR/SWIR/MIR and TIR reflectance spectra.
   `AuScope NVCL - Building Australia's mineralogy database <https://www.auscope.org.au/nvcl>`_
      The National Virtual Core Library was enabled by NCRIS via AuScope.

.. toctree::
   :maxdepth: 3
   :hidden:
   :caption: Getting Started

   installation
   introduction
   citation

.. toctree::
   :maxdepth: 3
   :hidden:
   :caption: Reference

   source/nvcl_kit

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
